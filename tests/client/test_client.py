import asyncio
import datetime
from asyncio import StreamReader

import pytest

from givenergy_modbus.client.client import Client
from givenergy_modbus.model import TimeSlot
from givenergy_modbus.pdu import WriteHoldingRegisterRequest, WriteHoldingRegisterResponse


async def test_expected_response():
    client = Client(host='foo', port=4321)
    assert client.expected_responses == {}
    req = WriteHoldingRegisterRequest(register=35, value=20)
    client.reader = StreamReader()
    network_consumer = asyncio.create_task(client._task_network_consumer())

    # enqueue the request
    send_and_wait = asyncio.create_task(client.send_request_and_await_response(req, timeout=0.1, retries=2))

    # simulate the message being transmitted
    tx_msg, tx_fut = await client.tx_queue.get()
    assert tx_msg == req.encode()
    client.tx_queue.task_done()
    tx_fut.set_result(True)

    # simulate receiving a response, which enables the consumer task to mark response_future as done
    client.reader.feed_data(WriteHoldingRegisterResponse(inverter_serial_number='', base_register=35, register_values=[20]).encode())
    client.reader.feed_eof()

    # check the response
    res, _ = await asyncio.gather(send_and_wait, network_consumer)

    assert len(client.expected_responses) == 1
    assert res.shape_hash() in client.expected_responses.keys()
    expected_res_future = client.expected_responses[res.shape_hash()]
    assert expected_res_future._state == 'FINISHED'
    expected_res = await expected_res_future
    assert expected_res.shape_hash() == res.shape_hash()
    assert expected_res == res


def test_timeslot():
    ts = TimeSlot(datetime.time(4, 5), datetime.time(9, 8))
    assert ts == TimeSlot(start=datetime.time(4, 5), end=datetime.time(9, 8))
    assert ts == TimeSlot(datetime.time(4, 5), datetime.time(9, 8))
    assert ts == TimeSlot.from_components(4, 5, 9, 8)
    assert ts == TimeSlot.from_repr(405, 908)
    assert ts == TimeSlot.from_repr('405', '908')
    assert TimeSlot(datetime.time(0, 2), datetime.time(0, 2)) == TimeSlot.from_repr(2, 2)
    with pytest.raises(ValueError, match='hour must be in 0..23'):
        TimeSlot.from_repr(999999, 999999)
    with pytest.raises(ValueError, match='minute must be in 0..59'):
        TimeSlot.from_repr(999, 888)
    with pytest.raises(ValueError, match='hour must be in 0..23'):
        TimeSlot.from_components(99, 88, 77, 66)
    with pytest.raises(ValueError, match='minute must be in 0..59'):
        TimeSlot.from_components(11, 22, 11, 66)

    ts = TimeSlot(datetime.time(12, 34), datetime.time(23, 45))
    assert ts == TimeSlot(start=datetime.time(12, 34), end=datetime.time(23, 45))
    assert ts == TimeSlot(datetime.time(12, 34), datetime.time(23, 45))
    assert ts == TimeSlot.from_components(12, 34, 23, 45)
    assert ts == TimeSlot.from_repr(1234, 2345)
    assert ts == TimeSlot.from_repr('1234', '2345')
    with pytest.raises(ValueError, match='hour must be in 0..23'):
        assert ts == TimeSlot.from_components(43, 21, 54, 32)
    with pytest.raises(ValueError, match='hour must be in 0..23'):
        assert ts == TimeSlot.from_repr(4321, 5432)
    with pytest.raises(ValueError, match='hour must be in 0..23'):
        assert ts == TimeSlot.from_repr('4321', '5432')

    ts = TimeSlot(datetime.time(0, 30), datetime.time(0, 40))
    assert 29 not in ts
    assert 30 in ts
    assert 39 in ts
    assert 40 not in ts
    assert datetime.time(0, 29) not in ts
    assert datetime.time(0, 30) in ts
    assert datetime.time(0, 39) in ts
    assert datetime.time(0, 40) not in ts
    
    ts = TimeSlot(datetime.time(11, 30), datetime.time(13, 40))
    assert 1129 not in ts
    assert 1131 in ts
    assert 1200 in ts
    assert 1339 in ts
    assert 1340 not in ts
    assert datetime.time(0, 29) not in ts
    assert datetime.time(11, 29) not in ts
    assert datetime.time(11, 31) in ts
    assert datetime.time(12, 00) in ts
    assert datetime.time(13, 00) in ts
    assert datetime.time(13, 40) not in ts

    ts = TimeSlot(datetime.time(23, 30), datetime.time(5, 30))
    assert 2329 not in ts
    assert 2331 in ts
    assert 2359 in ts
    assert 0 in ts
    assert 529 in ts
    assert 530 not in ts
