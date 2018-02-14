# Copyright 2018 Palantir Technologies, Inc.
from jsonrpc.jsonrpc2 import JSONRPC20Request


#
# def test_fail_to_parse(rpc_manager):
#     wfile = rpc_manager.rfile
#     rfile = rpc_manager.wfile
#     wfile.write(unicode("test"))
#     wfile.write(unicode('"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {}'))
#     messages = rpc_manager.get_messages()
#     assert messages.next() == "test"
