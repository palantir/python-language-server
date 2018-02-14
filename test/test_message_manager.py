# Copyright 2018 Palantir Technologies, Inc.
from jsonrpc.jsonrpc2 import JSONRPC20Request

CONTENT_HEADER='Content-Length: {}\r\nContent-Type: application/vscode-jsonrpc; charset=utf8\r\n\r\n'
SIMPLE_MESSAGE='{"jsonrpc":"2.0","id":0,"method":"initialize","params":{}}\n'


# def test_recieve_message(message_manager):
#     manager, rx, tx_pipe = message_manager
#     tx_pipe.write(CONTENT_HEADER.format(len(SIMPLE_MESSAGE)).encode('utf-8'))
#     tx_pipe.write(SIMPLE_MESSAGE.encode('utf-8'))
#     messages = manager.get_messages()
#     assert isinstance(messages.next(), JSONRPC20Request)
