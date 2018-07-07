# Copyright 2017 Palantir Technologies, Inc.
import hashlib
import logging
import threading
import re
import sys
import time

from mypy import dmypy, dmypy_server, fscache, main, version

from pyls import hookimpl, lsp, uris

log = logging.getLogger(__name__)

MYPY_RE = re.compile(r"([^:]+):(?:(\d+):)?(?:(\d+):)? (\w+): (.*)")


@hookimpl
def pyls_initialize(workspace):
    log.info("Launching mypy server")
    thread = threading.Thread(target=launch_daemon, args=([], workspace))
    thread.daemon = True
    thread.start()


@hookimpl
def pyls_lint(document):
    args = _parse_daemon_args([document.path])
    log.info("Sending request to mypy daemon")
    response = dmypy.request('run', version=version.__version__, args=args.flags)
    log.info("Got response from mypy daemon: %s", response)

    # If the daemon signals that a restart is necessary, do it
    if 'restart' in response:
        # TODO(gatesn): figure out how to restart daemon
        log.error("Need to restart daemon")
        sys.exit("Need to restart mypy daemon")
        # print('Restarting: {}'.format(response['restart']))
        # restart_server(args, allow_sources=True)
        # response = request('run', version=version.__version__, args=args.flags)

    try:
        stdout, stderr, status_code = response['out'], response['err'], response['status']
        if stderr:
            log.warning("Mypy stderr: %s", stderr)
        return _process_mypy_output(stdout, document)
    except KeyError:
        log.error("Unknown mypy daemon response: %s", response)


def _process_mypy_output(stdout, document):
    for line in stdout.splitlines():
        result = re.match(MYPY_RE, line)
        if not result:
            log.warning("Failed to parse mypy output: %s", line)
            continue

        _, lineno, offset, level, msg = result.groups()
        lineno = (int(lineno) or 1) - 1
        offset = (int(offset) or 1) - 1  # mypy says column numbers are zero-based, but they seem not to be

        if level == "error":
            severity = lsp.DiagnosticSeverity.Error
        elif level == "warning":
            severity = lsp.DiagnosticSeverity.Warning
        elif level == "note":
            severity = lsp.DiagnosticSeverity.Information
        else:
            log.warning("Unknown mypy severity: %s", level)
            continue

        diag = {
            'source': 'mypy',
            'range': {
                'start': {'line': lineno, 'character': offset},
                # There may be a better solution, but mypy does not provide end
                'end': {'line': lineno, 'character': offset + 1}
            },
            'message': msg,
            'severity': severity
        }

        # Try and guess the end of the word that mypy is highlighting
        word = document.word_at_position(diag['range']['start'])
        if word:
            diag['range']['end']['character'] = offset + len(word)

        yield diag


def launch_daemon(raw_args, workspace):
    """Launch the mypy daemon in-process."""
    args = _parse_daemon_args(raw_args)
    _sources, options = main.process_options(
        ['-i'] + args.flags, require_targets=False, server_options=True
    )
    server = dmypy_server.Server(options)
    server.fscache = PylsFileSystemCache(workspace)
    server.serve()
    log.error("mypy daemon stopped serving requests")


def _parse_daemon_args(raw_args):
    return dmypy.parser.parse_args([
        'run', '--',
        '--show-traceback',
        '--follow-imports=skip',
        '--show-column-numbers',
    ] + raw_args)


class PylsFileSystemCache(fscache.FileSystemCache):
    """Patched implementation of FileSystemCache to read from workspace."""

    def __init__(self, workspace):
        self._workspace = workspace
        self._checksums = {}
        self._mtimes = {}
        super(PylsFileSystemCache, self).__init__()

    def stat(self, path):
        stat = super(PylsFileSystemCache, self).stat(path)

        uri = uris.from_fs_path(path)
        document = self._workspace.documents.get(uri)
        if document:
            size = len(document.source.encode('utf-8'))
            mtime = self._workspace.get_document_mtime(uri)
            return MutableOsState(stat, {'st_size': size, 'st_mtime': mtime})

        return stat

    def read(self, path):
        document = self._workspace.documents.get(uris.from_fs_path(path))
        if document:
            # We need to return bytes
            data = document.source.encode('utf-8')
            return data
        return super(PylsFileSystemCache, self).read(path)

    def md5(self, path):
        document = self._workspace.documents.get(uris.from_fs_path(path))
        if document:
            return hashlib.md5(document.source.encode('utf-8')).hexdigest()
        return super(PylsFileSystemCache, self).read(path)


class MutableOsState(object):

    def __init__(self, stat_result, overrides):
        self._stat_result = stat_result
        self._overrides = overrides

    def __getattr__(self, item):
        if item in self._overrides:
            return self._overrides[item]
        return getattr(self._stat_result, item)
