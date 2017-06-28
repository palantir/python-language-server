# Copyright 2017 Palantir Technologies, Inc.
import argparse
import json
import logging
import logging.config
import sys
from . import language_server
from .python_ls import PythonLanguageServer

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
        "--log-file",
        help="Redirect logs to the given file instead of writing to stderr."
        "Has no effect if used with --log-config."
    )
    parser.add_argument(
        "--log-config",
        help="Path to a JSON file containing Python logging config."
    )


def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()

    if args.log_config:
        with open(args.log_config, 'r') as f:
            logging.config.dictConfig(json.load(f))
    elif args.log_file:
        logging.basicConfig(filename=args.log_file, level=logging.WARNING, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT)

    if args.tcp:
        language_server.start_tcp_lang_server(args.host, args.port, PythonLanguageServer)
    else:
        language_server.start_io_lang_server(sys.stdin, sys.stdout, PythonLanguageServer)
