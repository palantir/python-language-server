# Copyright 2017 Palantir Technologies, Inc.
import argparse
import logging
import logging.config
import sys

try:
    import ujson as json
except Exception:  # pylint: disable=broad-except
    import json

from .python_ls import (PythonLanguageServer, start_io_lang_server,
                        start_tcp_lang_server)

LOG_FORMAT = "%(asctime)s UTC - %(levelname)s - %(name)s - %(message)s"


def add_arguments(parser):
    parser.description = "Python Language Server"

    parser.add_argument(
        "--tcp", action="store_true",
        help="Use TCP server instead of stdio"
    )
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="Bind to this address"
    )
    parser.add_argument(
        "--port", type=int, default=2087,
        help="Bind to this port"
    )
    parser.add_argument(
        '--check-parent-process', action="store_true",
        help="Check whether parent process is still alive using os.kill(ppid, 0) "
        "and auto shut down language server process when parent process is not alive."
        "Note that this may not work on a Windows machine."
    )

    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "--log-config",
        help="Path to a JSON file containing Python logging config."
    )
    log_group.add_argument(
        "--log-file",
        help="Redirect logs to the given file instead of writing to stderr."
        "Has no effect if used with --log-config."
    )

    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help="Increase verbosity of log output, overrides log config file"
    )


def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()
    _configure_logger(args.verbose, args.log_config, args.log_file)

    if args.tcp:
        start_tcp_lang_server(args.host, args.port, args.check_parent_process,
                              PythonLanguageServer)

    start_io_lang_server(sys.stdin.buffer, sys.stdout.buffer,
                         args.check_parent_process, PythonLanguageServer)


def _configure_logger(verbose=0, log_config=None, log_file=None):
    root_logger = logging.root

    if log_config:
        with open(log_config, 'r') as f:
            logging.config.dictConfig(json.load(f))
    else:
        formatter = logging.Formatter(LOG_FORMAT)
        if log_file:
            log_handler = logging.handlers.RotatingFileHandler(
                log_file, mode='a', maxBytes=50*1024*1024,
                backupCount=10, encoding=None, delay=0
            )
        else:
            log_handler = logging.StreamHandler()
        log_handler.setFormatter(formatter)
        root_logger.addHandler(log_handler)

    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    root_logger.setLevel(level)


if __name__ == '__main__':
    main()
