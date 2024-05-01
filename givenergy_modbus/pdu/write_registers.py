import logging
from abc import ABC

from ..codec import (
    PayloadDecoder,
    PayloadEncoder,
)
from ..exceptions import (
    InvalidPduState,
)
from .transparent import (
    TransparentMessage,
    TransparentRequest,
    TransparentResponse,
)

_logger = logging.getLogger(__name__)

class WriteHoldingRegister(TransparentMessage, ABC):
    """Request & Response PDUs for function #6/Write Holding Register."""

    transparent_function_code = 6

    register: int
    value: int

    def __init__(self, register: int, value: int, *args, **kwargs):
        if len(args) == 2:
            kwargs["register"] = args[0]
            kwargs["value"] = args[1]
        kwargs["slave_address"] = kwargs.get("slave_address", 0x11)
        super().__init__(**kwargs)
        if not isinstance(register, int):
            raise ValueError(f"Register type {type(register)} is unacceptable")
        self.register = register
        if not isinstance(value, int):
            raise ValueError(f"Register value {type(value)} is unacceptable")
        self.value = value

    def __str__(self) -> str:
        if self.register is not None and self.value is not None:
            return (
                f"{self.function_code}:{self.transparent_function_code}/{self.__class__.__name__}"
                f"({'ERROR ' if self.error else ''}{self.register} -> "
                f"{self.value}/0x{self.value:04x})"
            )
        else:
            return super().__str__()

    def __eq__(self, o: object) -> bool:
        return (
            isinstance(o, type(self))
            and self.has_same_shape(o)
            and o.register == self.register
            and o.value == self.value
        )

    def _encode_function_data(self):
        super()._encode_function_data()
        self._builder.add_16bit_uint(self.register)
        self._builder.add_16bit_uint(self.value)
        self._update_check_code()

    @classmethod
    def decode_transparent_function(
        cls, decoder: PayloadDecoder, **attrs
    ) -> "WriteHoldingRegister":
        attrs["register"] = decoder.decode_16bit_uint()
        attrs["value"] = decoder.decode_16bit_uint()
        attrs["check"] = decoder.decode_16bit_uint()
        return cls(**attrs)

    def _extra_shape_hash_keys(self) -> tuple:
        return super()._extra_shape_hash_keys() + (self.register,)

    def ensure_valid_state(self):
        """Sanity check our internal state."""
        super().ensure_valid_state()
        if self.register is None:
            raise InvalidPduState("Register must be set", self)
        if self.value is None:
            raise InvalidPduState("Register value must be set", self)
        elif 0 > self.value > 0xFFFF:
            raise InvalidPduState(
                f"Value {self.value}/0x{self.value:04x} must be an unsigned 16-bit int",
                self,
            )


class WriteHoldingRegisterRequest(WriteHoldingRegister, TransparentRequest):
    """Concrete PDU implementation for handling function #6/Write Holding Register request messages."""

    def ensure_valid_state(self):
        """Sanity check our internal state."""
        super().ensure_valid_state()

    def _update_check_code(self):
        crc_builder = PayloadEncoder()
        crc_builder.add_8bit_uint(self.slave_address)
        crc_builder.add_8bit_uint(self.transparent_function_code)
        crc_builder.add_16bit_uint(self.register)
        crc_builder.add_16bit_uint(self.value)
        self.check = crc_builder.crc
        self.check = int.from_bytes(self.check.to_bytes(2, "little"), "big")
        self._builder.add_16bit_uint(self.check)

    def expected_response(self):
        return WriteHoldingRegisterResponse(
            register=self.register, value=self.value, slave_address=self.slave_address
        )


class WriteHoldingRegisterResponse(WriteHoldingRegister, TransparentResponse):
    """Concrete PDU implementation for handling function #6/Write Holding Register response messages."""

    def ensure_valid_state(self):
        """Sanity check our internal state."""
        super().ensure_valid_state()


__all__ = ()
