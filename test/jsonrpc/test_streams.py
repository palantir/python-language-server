# Copyright 2018 Palantir Technologies, Inc.
# pylint: disable=redefined-outer-name
from io import BytesIO
import mock
import pytest

from pyls.jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter


@pytest.fixture()
def rfile():
    return BytesIO()


@pytest.fixture()
def wfile():
    return BytesIO()


@pytest.fixture()
def reader(rfile):
    return JsonRpcStreamReader(rfile)


@pytest.fixture()
def writer(wfile):
    return JsonRpcStreamWriter(wfile, sort_keys=True)


def test_reader(rfile, reader):
    rfile.write(
        b'Content-Length: 49\r\n'
        b'Content-Type: application/vscode-jsonrpc; charset=utf8\r\n'
        b'\r\n'
        b'{"id": "hello", "method": "method", "params": {}}'
    )
    rfile.seek(0)

    consumer = mock.Mock()
    reader.listen(consumer)

    consumer.assert_called_once_with({
        'id': 'hello',
        'method': 'method',
        'params': {}
    })


def test_reader_bad_message(rfile, reader):
    rfile.write(b'Hello world')
    rfile.seek(0)

    # Ensure the listener doesn't throw
    consumer = mock.Mock()
    reader.listen(consumer)
    consumer.assert_not_called()


def test_reader_bad_json(rfile, reader):
    rfile.write(
        b'Content-Length: 8\r\n'
        b'Content-Type: application/vscode-jsonrpc; charset=utf8\r\n'
        b'\r\n'
        b'{hello}}'
    )
    rfile.seek(0)

    # Ensure the listener doesn't throw
    consumer = mock.Mock()
    reader.listen(consumer)
    consumer.assert_not_called()


def test_writer(wfile, writer):
    writer.write({
        'id': 'hello',
        'method': 'method',
        'params': {}
    })
    assert wfile.getvalue() == (
        b'Content-Length: 49\r\n'
        b'Content-Type: application/vscode-jsonrpc; charset=utf8\r\n'
        b'\r\n'
        b'{"id": "hello", "method": "method", "params": {}}'
    )


def test_writer_bad_message(wfile, writer):
    # A datetime isn't serializable, ensure the write method doesn't throw
    import datetime
    writer.write(datetime.datetime.now())
    assert wfile.getvalue() == b''
