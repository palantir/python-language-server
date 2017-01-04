# Copyright 2017 Palantir Technologies, Inc.
import argparse
import logging
import time
import sys
import language_server
from python_ls import PythonLanguageServer


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


def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()

    # Configure logging to DEBUG and UTC
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s UTC - %(levelname)s - %(name)s - %(message)s")
    logging.Formatter.converter = time.gmtime

    if args.tcp:
        language_server.start_tcp_lang_server(args.host, args.port, PythonLanguageServer)
    else:
        language_server.start_io_lang_server(sys.stdin, sys.stdout, PythonLanguageServer)
