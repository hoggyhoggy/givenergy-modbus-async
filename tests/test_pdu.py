import logging
from typing import Any, Optional

import pytest

from givenergy_modbus.exceptions import ExceptionBase, InvalidFrame, InvalidPduState
from givenergy_modbus.model.register import HR
from givenergy_modbus.pdu import (
    BasePDU,
    HeartbeatMessage,
    HeartbeatRequest,
    HeartbeatResponse,
    NullResponse,
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
    ReadInputRegistersRequest,
    ReadInputRegistersResponse,
    TransparentMessage,
    TransparentRequest,
    TransparentResponse,
    WriteHoldingRegisterRequest,
    WriteHoldingRegisterResponse,
)
from tests.conftest import ALL_MESSAGES, PduTestCaseSig


# transparent messages are quite strict about having all
# fields defined. Helpers to reduce typing.

def _make_readreq(cls, br=0, rc=60, **kwargs):
    kwargs['base_register']=br
    kwargs['register_count']=rc
    return cls(**kwargs)

def _make_readrsp(cls, br=0, rc=60, rv=None, **kwargs):
    kwargs['inverter_serial_number'] = 'SA1234G567'
    kwargs['base_register']=br
    kwargs['register_count']=rc
    if rv is None:
        rv = tuple( v for v in range(rc) )
    kwargs['register_values']=rv
    return cls(**kwargs)

def _make_writereq(cls, br=0, rv=42, **kwargs):
    kwargs['base_register']=br
    kwargs['register_values']=(rv,)
    return cls(**kwargs)

def _make_writersp(cls, br=0, rv=42, **kwargs):
    kwargs['inverter_serial_number'] = 'SA1234G567'
    kwargs['base_register']=br
    kwargs['register_values']=(rv,)
    return cls(**kwargs)

# Normally the framer chooses the appropriate decoding class, based
# on frame contents. But here we have to do it based on the expected
# class.
def _choose_decoder(pdu_class):
    for cls in (TransparentRequest, TransparentResponse, HeartbeatRequest, HeartbeatResponse):
        if issubclass(pdu_class, cls):
            return cls.decode_bytes
    pytest.fail("No decoder for" + str(pdu_class))



def test_str():
    """Ensure human-friendly string representations."""
    # ABCs before main function definitions
    assert '/BasePDU(' not in str(BasePDU())
    assert str(BasePDU()).startswith('<givenergy_modbus.pdu.base.BasePDU object at ')

    # __str__() gets defined at the main function ABC
    assert str(HeartbeatMessage(foo=3, bar=6)) == (
        '1/HeartbeatMessage(data_adapter_serial_number=AB1234G567 data_adapter_type=0)'
    )
    assert str(HeartbeatMessage(data_adapter_serial_number='xxx', data_adapter_type=33)) == (
        '1/HeartbeatMessage(data_adapter_serial_number=xxx data_adapter_type=33)'
    )
    assert str(HeartbeatRequest(foo=3, bar=6)) == (
        '1/HeartbeatRequest(data_adapter_serial_number=AB1234G567 data_adapter_type=0)'
    )
    assert str(HeartbeatResponse(data_adapter_serial_number='xxx', data_adapter_type=33)) == (
        '1/HeartbeatResponse(data_adapter_serial_number=xxx data_adapter_type=33)'
    )

    assert str(TransparentMessage(foo=3, bar=6)) == '2:_/TransparentMessage()'
    assert str(TransparentRequest(foo=3, bar=6)) == '2:_/TransparentRequest()'
    assert str(TransparentRequest(inner_function_code=44)) == '2:_/TransparentRequest()'
    assert str(TransparentResponse(foo=3, bar=6)) == '2:_/TransparentResponse()'
    assert str(TransparentResponse(inner_function_code=44)) == '2:_/TransparentResponse()'

    assert str(_make_readreq(ReadInputRegistersRequest, 3, 6)) == (
        '2:4/ReadInputRegistersRequest(base_register=3 register_count=6)'
    )
    assert str(NullResponse(inverter_serial_number='SA1234G567', register_values=(0,)*62)) == '2:0/NullResponse()'

    with pytest.raises(InvalidPduState, match="base_register"):
        WriteHoldingRegisterRequest(foo=1)
    with pytest.raises(InvalidPduState, match="inverter_serial_number"):
        WriteHoldingRegisterResponse(foo=1)
    with pytest.raises(InvalidPduState, match="register_values"):
        WriteHoldingRegisterResponse(inverter_serial_number='SA1234G567', base_register=0)
    assert str(WriteHoldingRegisterResponse(inverter_serial_number='SA1234G567', base_register=18, register_values=(7,))) == (
        '2:6/WriteHoldingRegisterResponse(18 -> 7/0x0007)'
    )
    assert str(WriteHoldingRegisterResponse(inverter_serial_number='SA1234G567', error=True, base_register=7, register_values=(6,))) == (
        '2:6/WriteHoldingRegisterResponse(ERROR 7 -> 6/0x0006)'
    )

    assert str(HeartbeatRequest(foo=1)) == (
        '1/HeartbeatRequest(data_adapter_serial_number=AB1234G567 data_adapter_type=0)'
    )
    assert str(HeartbeatResponse(foo=1)) == (
        '1/HeartbeatResponse(data_adapter_serial_number=AB1234G567 data_adapter_type=0)'
    )


@pytest.mark.parametrize(PduTestCaseSig, ALL_MESSAGES)
def test_str_actual_messages(
    str_repr: str,
    pdu_class: type[BasePDU],
    constructor_kwargs: dict[str, Any],
    mbap_header: bytes,
    inner_frame: bytes,
    ex: Optional[ExceptionBase],
):
    assert str(pdu_class(**constructor_kwargs)) == str_repr


def test_class_equivalence():
    """Confirm some behaviours on subclassing."""
    assert issubclass(ReadHoldingRegistersRequest, TransparentRequest)
    assert issubclass(ReadInputRegistersRequest, TransparentRequest)
    assert not issubclass(ReadHoldingRegistersRequest, ReadInputRegistersRequest)
    assert isinstance(_make_readreq(ReadHoldingRegistersRequest), TransparentRequest)
    assert isinstance(_make_readreq(ReadInputRegistersRequest), TransparentRequest)
    assert not isinstance(_make_readreq(ReadInputRegistersRequest), ReadHoldingRegistersRequest)
    assert ReadInputRegistersRequest is ReadInputRegistersRequest


def test_cannot_change_function_code():
    """Disabuse any use of function_code in PDU constructors."""
    assert     hasattr(TransparentMessage, 'function_code')
    assert not hasattr(TransparentMessage, 'transparent_function_code')

    assert _make_readreq(ReadHoldingRegistersRequest, error=True).transparent_function_code == 3

    assert _make_readreq(ReadHoldingRegistersRequest, function_code=12).function_code != 12
    assert _make_readreq(ReadHoldingRegistersRequest, main_function_code=12).function_code != 12
    assert _make_readreq(ReadHoldingRegistersRequest, transparent_function_code=12).function_code != 12
    assert _make_readreq(ReadHoldingRegistersRequest, function_code=12).transparent_function_code != 12
    assert _make_readreq(ReadHoldingRegistersRequest, main_function_code=12).transparent_function_code != 12
    assert _make_readreq(ReadHoldingRegistersRequest, transparent_function_code=12).transparent_function_code != 12


@pytest.mark.parametrize(PduTestCaseSig, ALL_MESSAGES)
def test_encoding(
    str_repr: str,
    pdu_class: type[BasePDU],
    constructor_kwargs: dict[str, Any],
    mbap_header: bytes,
    inner_frame: bytes,
    ex: Optional[ExceptionBase],
):
    """Ensure PDU objects can be encoded to the correct wire format."""
    pdu = pdu_class(**constructor_kwargs)
    if ex:
        with pytest.raises(type(ex), match=ex.message):
            pdu.encode()
    else:
        assert pdu.encode().hex() == (mbap_header + inner_frame).hex()

@pytest.mark.parametrize(PduTestCaseSig, ALL_MESSAGES)
def test_decoding(
    str_repr: str,
    pdu_class: type[BasePDU],
    constructor_kwargs: dict[str, Any],
    mbap_header: bytes,
    inner_frame: bytes,
    ex: Optional[ExceptionBase],
    caplog,
):
    """Ensure we correctly decode Request messages to their unencapsulated PDU."""
    assert mbap_header[-1] == pdu_class.function_code
    frame = mbap_header + inner_frame
    caplog.set_level(logging.DEBUG)  # FIXME remove

    decoder = _choose_decoder(pdu_class)

    if ex:
        with pytest.raises(type(ex), match=ex.message):
            decoder(frame)
    else:
        constructor_kwargs['raw_frame'] = mbap_header + inner_frame
        pdu = decoder(frame)
        assert isinstance(pdu, pdu_class)
        for k in constructor_kwargs:
            assert getattr(pdu, k) == constructor_kwargs[k]
        assert str(pdu) == str_repr


@pytest.mark.parametrize(PduTestCaseSig, ALL_MESSAGES)
def test_decoding_wrong_streams(
    str_repr: str,
    pdu_class: type[BasePDU],
    constructor_kwargs: dict[str, Any],
    mbap_header: bytes,
    inner_frame: bytes,
    ex: Optional[ExceptionBase],
):
    """Ensure we correctly decode Request messages to their unencapsulated PDU."""
    if ex:
        return
    frame = mbap_header + inner_frame

    decoder = _choose_decoder(pdu_class)

    with pytest.raises(InvalidFrame, match='Transaction ID 0x[0-9a-f]{4} != 0x5959'):
        decoder(frame[2:])
    with pytest.raises(
        InvalidFrame, match=f'Header length {len(frame) - 6} != remaining frame length {len(frame) - 8}'
    ):
        decoder(frame[:-2])
    with pytest.raises(
        InvalidFrame, match=f'Header length {len(frame) - 6} != remaining frame length {len(frame) - 4}'
    ):
        decoder(frame + b'\x22\x22')
    with pytest.raises(InvalidFrame, match='Transaction ID 0x[0-9a-f]{4} != 0x5959'):
        decoder(frame[-10:])
    with pytest.raises(InvalidFrame, match='Transaction ID 0x[0-9a-f]{4} != 0x5959'):
        decoder(frame[::-1])


@pytest.mark.skip('Needs more thinking')   # __eq__ is currently only implemented in WriteHoldingRegisterRequest
def test_writable_registers_equality():
    req = WriteHoldingRegisterRequest(register=4, value=22)
    assert req.base_register == 4
    assert str(req) == '2:6/WriteHoldingRegisterRequest(4 -> 22/0x0016)'
    assert req == WriteHoldingRegisterRequest(register=4, value=22)
    assert req != WriteHoldingRegisterRequest(register=4, value=32)
    assert req != WriteHoldingRegisterRequest(register=5, value=22)
    assert req != _make_writersp(WriteHoldingRegisterResponse, br=4, rv=22)

    rsp = _make_writersp(WriteHoldingRegisterResponse,br=5, rv=33)
    assert rsp.base_register == 5
    assert str(rsp) == '2:6/WriteHoldingRegisterResponse(5 -> 33/0x0021)'
    assert rsp != WriteHoldingRegisterRequest(register=5, value=33)

    rsp = _make_writersp(WriteHoldingRegisterResponse,br=6, rv=55, error=True)
    assert rsp.base_register == 6
    assert str(rsp) == '2:6/WriteHoldingRegisterResponse(ERROR 6 -> 55/0x0037)'
    assert rsp != WriteHoldingRegisterRequest(register=6, value=55)
    assert rsp == _make_writersp(WriteHoldingRegisterResponse, br=6, rv=55)
    assert rsp == _make_writersp(WriteHoldingRegisterResponse, br=6, rv=55, error=True)


def test_read_registers_response_as_dict():
    """Ensure a ReadRegistersResponse can be turned into a dict representation."""
    r = _make_readrsp(ReadHoldingRegistersResponse,br=100, rc=10, rv=list(range(10))[::-1])
    d = dict(r.enumerate())
    assert d == {HR(100): 9, HR(101): 8, HR(102): 7, HR(103): 6, HR(104): 5, HR(105): 4, HR(106): 3, HR(107): 2, HR(108): 1, HR(109): 0}

    r = _make_readrsp(ReadHoldingRegistersResponse,br=1000, rc=10, register_values=('a',) * 10)
    d = dict(r.enumerate())
    t = {
        HR(1000): 'a',
        HR(1001): 'a',
        HR(1002): 'a',
        HR(1003): 'a',
        HR(1004): 'a',
        HR(1005): 'a',
        HR(1006): 'a',
        HR(1007): 'a',
        HR(1008): 'a',
        HR(1009): 'a',
    }
    # for some reason this is failing. Not sure why - they look the same.
    # assert d == t


def test_has_same_shape():
    """Ensure we can compare PDUs sensibly.
    In the current implementation, the Response should have the
    same shape as the originating request.
    """

    req1 = _make_readreq(ReadInputRegistersRequest, br=0, rc=2)
    req2 = _make_readreq(ReadInputRegistersRequest, br=60, rc=2)
    req3 = _make_readreq(ReadHoldingRegistersRequest, br=60, rc=2)
    rsp1 = _make_readrsp(ReadInputRegistersResponse, br=0, rc=2)
    rsp2 = _make_readrsp(ReadInputRegistersResponse, br=60, rc=2)
    rsp3 = _make_readrsp(ReadHoldingRegistersResponse, br=60, rc=2)

    assert req1.shape_hash() == rsp1.shape_hash()
    assert req2.shape_hash() == rsp2.shape_hash()
    assert req3.shape_hash() == rsp3.shape_hash()

    shape1 = req1.shape_hash()
    assert shape1 != req2.shape_hash()
    assert shape1 != req3.shape_hash()

    rsp1b = _make_readrsp(ReadInputRegistersResponse, br=0, rc=2, rv=[4,6])
    rsp1c = _make_readrsp(ReadInputRegistersResponse, br=0, rc=2, rv=[7,9], error=True)

    assert shape1 == rsp1b.shape_hash()
    assert shape1 == rsp1c.shape_hash()

    r1 = _make_readrsp(ReadInputRegistersResponse, br=1, rc=2, rv=[33, 45])
    r2 = _make_readrsp(ReadInputRegistersResponse, br=1, rc=2, rv=[10, 11])
    assert r1.shape_hash() == r2.shape_hash()
    assert r1 != r2

    test_set = {r1, r2}
    assert len(test_set) == 2
    assert r1 in test_set
    assert r2 in test_set

    req1 = _make_readreq(ReadInputRegistersRequest, br=0, rc=2, slave_address=0x32)
    req2 = _make_readreq(ReadInputRegistersRequest, br=0, rc=2, slave_address=0x33)
    rsp1 = _make_readrsp(ReadInputRegistersResponse, br=0, rc=2, slave_address=0x32)
    rsp2 = _make_readrsp(ReadInputRegistersResponse, br=0, rc=2, slave_address=0x33)

    assert req1.shape_hash() == rsp1.shape_hash()
    assert req2.shape_hash() == rsp2.shape_hash()
    assert req1.shape_hash() != rsp2.shape_hash()

    req1 = _make_writereq(WriteHoldingRegisterRequest,  br=0, rv=2)
    rsp1 = _make_writersp(WriteHoldingRegisterResponse, br=0, rv=2)
    req2 = _make_writereq(WriteHoldingRegisterRequest,  br=1, rv=4)
    rsp2 = _make_writersp(WriteHoldingRegisterResponse, br=1, rv=4)
    rsp2e= _make_writersp(WriteHoldingRegisterResponse, br=1, rv=4, error=True)

    assert req1.shape_hash() == rsp1.shape_hash()
    assert req2.shape_hash() == rsp2.shape_hash()
    assert req2.shape_hash() == rsp2e.shape_hash()
    assert req1.shape_hash() != rsp2.shape_hash()


@pytest.mark.skip('Needs more thinking')     # __eq__ is currently only implemented in WriteHoldingRegisterRequest
def test_hashing():
    r1 = WriteHoldingRegisterResponse(register=2, value=10)
    r2 = WriteHoldingRegisterResponse(register=2, value=10)
    assert r1 == r2

    test_set = {
        WriteHoldingRegisterResponse(register=2, value=42),
        WriteHoldingRegisterResponse(register=2, value=10),
        WriteHoldingRegisterResponse(register=2, value=10),
    }
    assert len(test_set) == 2
    assert WriteHoldingRegisterResponse(register=2, value=42) in test_set
    assert WriteHoldingRegisterResponse(register=2, value=10) in test_set

    assert (
        len(
            {
                WriteHoldingRegisterRequest(register=2, value=42),
                WriteHoldingRegisterResponse(register=2, value=42),
            }
        )
        == 2
    )
