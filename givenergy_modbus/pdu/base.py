import logging
import struct
from abc import ABC
from typing import ClassVar

from ..codec import (
    PayloadDecoder,
    PayloadEncoder,
)
from ..exceptions import (
    InvalidFrame,
    InvalidPduState,
)

_logger = logging.getLogger(__name__)


class BasePDU(ABC):
    """Base of the PDU Message network_timeout_handler class tree.

    The Protocol Data Unit (PDU) defines the basic unit of message exchange for Modbus. It is routed to devices with
    specific addresses, and targets specific operations through function codes. This tree defines the hierarchy of
    functions, along with the attributes they specify and how they are encoded.

    The wire protocol does not distinguish between 'Request' and 'Response', so how to decode a given function
    code has to be decided in advance - the caller must decide whether they are client-like or server-like.

    The PDU classes are also codecs – they know how to convert between binary network frames and instantiated objects
    that can be manipulated programmatically.
    """

    _builder: PayloadEncoder
    function_code: ClassVar[int]
    data_adapter_serial_number: str = (
        "AB1234G567"  # for client requests this seems ignored
    )
    raw_frame: bytes

    def _set_attribute_if_present(self, attr: str, **kwargs):
        if attr in kwargs:
            setattr(self, attr, kwargs[attr])

    def __init__(self, **kwargs):
        self._set_attribute_if_present("data_adapter_serial_number", **kwargs)

    # encoding
    # encode() prepares the generic preamble, then calls upon the class-specific
    # _encode_function_data() to do message-specific part

    def encode(self) -> bytes:
        """Encode PDU message from instance attributes."""
        self._builder = PayloadEncoder()
        self._builder.add_string(self.data_adapter_serial_number, 10)
        self._encode_function_data()
        inner_frame = self._builder.payload
        mbap_header = struct.pack(
            ">HHHBB", 0x5959, 0x1, len(inner_frame) + 2, 0x1, self.function_code
        )
        self.raw_frame = mbap_header + inner_frame
        return self.raw_frame

    def _encode_function_data(self) -> None:
        """Complete function-specific encoding of the remainder of the PDU message."""
        raise NotImplementedError()

    # decoding
    # decode_bytes() decodes the generic preamble, then calls upon the class-specific
    # decode_main_function() to do the message-specific part. cls is already set to
    # a suitable decoder based on fid and message direction.

    @classmethod
    def decode_bytes(cls, data: bytes) -> "BasePDU":
        """Decode raw byte frame to populated PDU instance."""
        decoder = PayloadDecoder(data)

        t_id = decoder.decode_16bit_uint()
        if t_id != 0x5959:
            raise InvalidFrame(f"Transaction ID 0x{t_id:04x} != 0x5959", data)

        p_id = decoder.decode_16bit_uint()
        if p_id != 0x0001:
            raise InvalidFrame(f"Protocol ID 0x{p_id:04x} != 0x0001", data)

        header_len = decoder.decode_16bit_uint()
        remaining_frame_len = (
            decoder.remaining_bytes
        )  # includes 2 bytes for uid and function code
        if header_len != remaining_frame_len:
            raise InvalidFrame(
                f"Header length {header_len} != remaining frame length {remaining_frame_len}",
                data,
            )

        u_id = decoder.decode_8bit_uint()
        if u_id not in (0x00, 0x01):
            raise InvalidFrame(f"Unit ID 0x{u_id:02x} != 0x00/0x01", data)

        function_code = decoder.decode_8bit_uint()
        assert cls.function_code == function_code

        try:
            pdu = cls.decode_main_function(decoder)
            pdu.raw_frame = data
        except InvalidPduState:
            raise
        # except Exception as e:
        #     raise InvalidFrame(str(e), data)

        if not decoder.decoding_complete:
            _logger.error(
                f"Decoder did not fully consume frame for {pdu}: decoded {decoder.decoded_bytes}b but "
                f"packet header specified length={decoder.payload_size}. "
                f"Remaining payload: [{decoder.remaining_payload.hex()}]"
            )
        return pdu

    @classmethod
    def decode_main_function(cls, decoder: PayloadDecoder, **attrs) -> "BasePDU":
        raise NotImplementedError()


__all__ = ()
