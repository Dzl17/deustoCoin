from flask import template_rendered, url_for
from app import app
from web3 import (
    EthereumTesterProvider,
    Web3,
)
from contextlib import contextmanager
import pytest
import typing as ty
import json
import os
import ipfshttpclient.encoding
import ipfshttpclient.exceptions
import ipfshttpclient.utils
import cryptocompare


@pytest.fixture
def tester_provider():
    return EthereumTesterProvider()


@pytest.fixture
def eth_tester(tester_provider):
    return tester_provider.ethereum_tester


@pytest.fixture
def w3(tester_provider):
    return Web3(tester_provider)


@pytest.fixture(scope='module')
def test_client():
    flask_app = app

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()


@contextmanager
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


@pytest.fixture
def json_encoder():
    return ipfshttpclient.encoding.Json()


def test_dummy_encoder():
    dummy_encoder = ipfshttpclient.encoding.Dummy()

    for v in (b"123", b"4", b"ddjlflsdmlflsdfjlfjlfdsjldfs"):
        assert dummy_encoder.encode(v) == v

        assert list(dummy_encoder.parse_partial(v)) == [v]
    assert list(dummy_encoder.parse_finalize()) == []


def test_json_parse_partial(json_encoder):
    data1 = {'key1': 'value1'}
    data2 = {'key2': 'value2'}

    data1_binary = json.dumps(data1).encode("utf-8")
    assert list(json_encoder.parse_partial(data1_binary[:8])) == []
    assert list(json_encoder.parse_partial(data1_binary[8:])) == [data1]
    assert list(json_encoder.parse_finalize()) == []

    data2_binary = json.dumps(data2).encode("utf-8")
    data2_final = b"  " + data1_binary + b"  \r\n  " + data2_binary + b"  "
    assert list(json_encoder.parse_partial(data2_final)) == [data1, data2]
    assert list(json_encoder.parse_finalize()) == []

    with pytest.raises(ipfshttpclient.exceptions.DecodingError):
        list(json_encoder.parse_partial(b'{"hello": "\xc3ber world!"}'))
    assert list(json_encoder.parse_finalize()) == []


def test_json_with_newlines(json_encoder):
    data1 = '{"key1":\n"value1",\n'
    data2 = '"key2":\n\n\n"value2"\n}'

    data_expected = json.loads(data1 + data2)

    assert list(json_encoder.parse_partial(data1.encode("utf-8"))) == []
    assert list(json_encoder.parse_partial(data2.encode("utf-8"))) == [data_expected]
    assert list(json_encoder.parse_finalize()) == []


def test_json_parse_incomplete(json_encoder):
    list(json_encoder.parse_partial(b'{"bla":'))
    with pytest.raises(ipfshttpclient.exceptions.DecodingError):
        json_encoder.parse_finalize()

    list(json_encoder.parse_partial(b'{"\xc3'))  # Incomplete UTF-8 sequence
    with pytest.raises(ipfshttpclient.exceptions.DecodingError):
        json_encoder.parse_finalize()


def test_json_encode(json_encoder):
    data = ty.cast(
        ipfshttpclient.utils.json_dict_t,
        {'key': 'value with Ünicøde characters ☺'}
    )
    assert json_encoder.encode(data) == \
           b'{"key":"value with \xc3\x9cnic\xc3\xb8de characters \xe2\x98\xba"}'


def test_json_encode_invalid_surrogate(json_encoder):
    data = ty.cast(
        ipfshttpclient.utils.json_dict_t,
        {'key': 'value with Ünicøde characters and disallowed surrgate: \uDC00'}
    )
    with pytest.raises(ipfshttpclient.exceptions.EncodingError):
        json_encoder.encode(data)


def test_json_encode_invalid_type(json_encoder):
    data = ty.cast(
        ipfshttpclient.utils.json_dict_t,
        {'key': b'value that is not JSON encodable'}
    )

    with pytest.raises(ipfshttpclient.exceptions.EncodingError):
        json_encoder.encode(data)


def test_get_encoder_by_name():
    encoder = ipfshttpclient.encoding.get_encoding('json')
    assert encoder.name == 'json'


def test_get_invalid_encoder():
    with pytest.raises(ipfshttpclient.exceptions.EncoderMissingError):
        ipfshttpclient.encoding.get_encoding('fake')


def test_cryptocompare():
    valorUDC = cryptocompare.get_price('ETH').get('ETH').get('EUR')
    assert valorUDC > 0


def test_ropsten():
    web3 = Web3(Web3.HTTPProvider(os.environ.get('ROPSTEN_URL')))
    balance = web3.eth.getBalance(os.environ.get('TEST_ADDRESS'))
    fBalance = float(web3.fromWei(balance, "ether"))
    assert fBalance >= 0
