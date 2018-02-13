# Copyright 2018 Palantir Technologies, Inc.
from jsonrpc.jsonrpc2 import JSONRPC20Request

CONTENT_HEADER='Content-Length: {}\r\nContent-Type: application/vscode-jsonrpc; charset=utf8\r\n\r\n'
SIMPLE_MESSAGE='{"jsonrpc":"2.0","id":0,"method":"initialize","params":{}}\n'


def test_get_parse_message(rpc_manager):
    manager, tx_pipe, rx_pipe = rpc_manager
    tx_pipe.write(CONTENT_HEADER.format(len(SIMPLE_MESSAGE)).encode('utf-8'))
    tx_pipe.write(SIMPLE_MESSAGE.encode('utf-8'))
    messages = rpc_manager.get_messages()
    assert isinstance(messages.next(), JSONRPC20Request)

#
# def test_fail_to_parse(rpc_manager):
#     wfile = rpc_manager.rfile
#     rfile = rpc_manager.wfile
#     wfile.write(unicode("test"))
#     wfile.write(unicode('"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {}'))
#     messages = rpc_manager.get_messages()
#     assert messages.next() == "test"
