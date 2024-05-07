import logging
from abc import ABC

from givenergy_modbus_async.codec import (
    PayloadDecoder,
    PayloadEncoder,
)
from givenergy_modbus_async.exceptions import (
    InvalidPduState,
)
from givenergy_modbus_async.pdu.transparent import (
    TransparentMessage,
    TransparentRequest,
    TransparentResponse,
)

_logger = logging.getLogger(__name__)

# Canonical list of registers that are safe to write to.
WRITE_SAFE_REGISTERS = {
    20,   #ENABLE_CHARGE_TARGET
    27,   #BATTERY_POWER_MODE
    29,   #SOC_FORCE_ADJUST
    31,   #CHARGE_SLOT_2_START
    32,   #CHARGE_SLOT_2_END
    35,   #SYSTEM_TIME_YEAR
    36,   #SYSTEM_TIME_MONTH
    37,   #SYSTEM_TIME_DAY
    38,   #SYSTEM_TIME_HOUR
    39,   #SYSTEM_TIME_MINUTE
    40,   #SYSTEM_TIME_SECOND
    44,   #DISCHARGE_SLOT_2_START
    45,   #DISCHARGE_SLOT_2_END
    50,   #ACTIVE_POWER_RATE
    56,   #DISCHARGE_SLOT_1_START
    57,   #DISCHARGE_SLOT_1_END
    59,   #ENABLE_DISCHARGE
    94,   #CHARGE_SLOT_1_START
    95,   #CHARGE_SLOT_1_END
    96,   #ENABLE_CHARGE
    110,  #BATTERY_SOC_RESERVE
    111,  #BATTERY_CHARGE_LIMIT
    112,  #BATTERY_DISCHARGE_LIMIT
    114,  #BATTERY_DISCHARGE_MIN_POWER_RESERVE
    116,  #CHARGE_TARGET_SOC
    163,  #REBOOT
    242,  #CHARGE_TARGET_SOC_1
    243,  #CHARGE_SLOT_2_START
    244,  #CHARGE_SLOT_2_END
    245,  #CHARGE_TARGET_SOC_2
    246,  #CHARGE_SLOT_3_START
    247,  #CHARGE_SLOT_3_END
    248,  #CHARGE_TARGET_SOC_3
    249,  #CHARGE_SLOT_4_START
    250,  #CHARGE_SLOT_4_END
    251,  #CHARGE_TARGET_SOC_4
    252,  #CHARGE_SLOT_5_START
    253,  #CHARGE_SLOT_5_END
    254,  #CHARGE_TARGET_SOC_5
    255,  #CHARGE_SLOT_6_START
    256,  #CHARGE_SLOT_6_END
    257,  #CHARGE_TARGET_SOC_6
    258,  #CHARGE_SLOT_7_START
    259,  #CHARGE_SLOT_7_END
    260,  #CHARGE_TARGET_SOC_7
    261,  #CHARGE_SLOT_8_START
    262,  #CHARGE_SLOT_8_END
    263,  #CHARGE_TARGET_SOC_8
    264,  #CHARGE_SLOT_9_START
    265,  #CHARGE_SLOT_9_END
    266,  #CHARGE_TARGET_SOC_9
    267,  #CHARGE_SLOT_10_START
    268,  #CHARGE_SLOT_10_END
    269,  #CHARGE_TARGET_SOC_10
    272,  #DISCHARGE_TARGET_SOC_1
    275,  #DISCHARGE_TARGET_SOC_2
    276,  #DISCHARGE_SLOT_3_START
    277,  #DISCHARGE_SLOT_3_END
    278,  #DISCHARGE_TARGET_SOC_3
    279,  #DISCHARGE_SLOT_4_START
    280,  #DISCHARGE_SLOT_4_END
    281,  #DISCHARGE_TARGET_SOC_4
    282,  #DISCHARGE_SLOT_5_START
    283,  #DISCHARGE_SLOT_5_END
    284,  #DISCHARGE_TARGET_SOC_5
    285,  #DISCHARGE_SLOT_6_START
    286,  #DISCHARGE_SLOT_6_END
    287,  #DISCHARGE_TARGET_SOC_6
    288,  #DISCHARGE_SLOT_7_START
    289,  #DISCHARGE_SLOT_7_END
    290,  #DISCHARGE_TARGET_SOC_7
    291,  #DISCHARGE_SLOT_8_START
    292,  #DISCHARGE_SLOT_8_END
    293,  #DISCHARGE_TARGET_SOC_8
    294,  #DISCHARGE_SLOT_9_START
    295,  #DISCHARGE_SLOT_9_END
    296,  #DISCHARGE_TARGET_SOC_9
    297,  #DISCHARGE_SLOT_10_START
    298,  #DISCHARGE_SLOT_10_END
    299,  #DISCHARGE_TARGET_SOC_10
    313,  #BATTERY_CHARGE_LIMIT_AC
    314,  #BATTERY_DISCHARGE_LIMIT_AC
    318,  #BATTERY_PAUSE_MODE
    319,  #BATTERY_PAUSE_SLOT_START
    320,  #BATTERY_PAUSE_SLOT_END
    2040, #EMS enable plant control
    2044, #EMS discharge slot 1 start
    2045, #EMS end
    2046, #EMS target
    2047, #EMS discharge slot 2 start
    2048, #EMS end
    2049, #EMS target
    2050, #EMS discharge slot 3 start
    2051, #EMS end
    2052, #EMS target
    2053, #EMS charge slot 1 start
    2054, #EMS end
    2055, #EMS target
    2056, #EMS charge slot 2 start
    2057, #EMS end
    2058, #EMS target
    2059, #EMS charge slot 3 start
    2060, #EMS end
    2061, #EMS target
    2062, #EMS export slot 1 start
    2063, #EMS end
    2064, #EMS target
    2065, #EMS export slot 2 start
    2066, #EMS end
    2067, #EMS target
    2068, #EMS export slot 3 start
    2069, #EMS end
    2070, #EMS target
}


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
        if self.register not in WRITE_SAFE_REGISTERS:
            raise InvalidPduState(f"HR({self.register}) is not safe to write to", self)

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
        if self.register not in WRITE_SAFE_REGISTERS and not self.error:
            _logger.warning(f"{self} is not safe for writing")


__all__ = ()
