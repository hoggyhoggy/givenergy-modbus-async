import logging

from .codec import PayloadDecoder
from .base import BasePDU

_logger = logging.getLogger(__name__)


class HeartbeatMessage(BasePDU):
    """Root of the hierarchy for 1/Heartbeat function PDUs."""

    function_code = 1
    data_adapter_type: int

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data_adapter_type: int = kwargs.get("data_adapter_type", 0x00)

    def __str__(self) -> str:
        return (
            f"1/{self.__class__.__name__}("
            f"data_adapter_serial_number={self.data_adapter_serial_number} "
            f"data_adapter_type={self.data_adapter_type})"
        )

    def _encode_function_data(self):
        """Encode request PDU message and populate instance attributes."""
        self._builder.add_8bit_uint(self.data_adapter_type)

    @classmethod
    def decode_main_function(
        cls, decoder: PayloadDecoder, **attrs
    ) -> "HeartbeatMessage":
        attrs["data_adapter_serial_number"] = decoder.decode_string(10)
        attrs["data_adapter_type"] = decoder.decode_8bit_uint()
        return cls(**attrs)


class HeartbeatRequest(HeartbeatMessage):
    """PDU sent by remote server to check liveness of client."""

    def expected_response(self) -> "HeartbeatResponse":
        """Create an appropriate response for an incoming HeartbeatRequest."""
        return HeartbeatResponse(data_adapter_type=self.data_adapter_type)


class HeartbeatResponse(HeartbeatMessage):
    """PDU returned by client (within 5s) to confirm liveness."""

    def decode(self, data: bytes):
        """Decode response PDU message and populate instance attributes."""
        decoder = PayloadDecoder(data)
        self.data_adapter_serial_number = decoder.decode_string(10)
        self.data_adapter_type = decoder.decode_8bit_uint()
        _logger.debug(f"Successfully decoded {len(data)} bytes")

    def expected_response(self) -> None:
        """No replies expected for HeartbeatResponse."""


__all__ = ()
