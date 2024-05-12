"""Handle the various different flavours of transparent message.

The packing format is fairly regular. After the modbus framing comes:
 uint8[10] serial: 10 byte ascii serial number of dongle
 uint64 padding
 uint8 addr:      unit identifier
 uint8 func:      function to be performed
 uint8[10]:       inverter serial number (responses)
 uint16 base:     base register number (all except null)
 uint16 count:    number of registers (all except writeholdingregister messages, and null)
 uint16[] values: (all replies, and writeholdingregister request)
 uint16 crc:      crc
Encoding is big-endian, except the crc which seems to be little-endian ?

The crc is computed from 'addr' onwards.

One outlier message is the unsolicited NullResponse, which is just 62 * [0].

Note that this code is only really intended to wire-encode Requests and
wire-decode Responses - the other combinations only really fall out by
accident and are not tested. In particular, the crc calculation for Responses
is probably wrong.
"""

from enum import Flag, auto
import logging
from typing import ClassVar, Iterator

from ..codec import PayloadEncoder, PayloadDecoder
from ..exceptions import InvalidPduState
from .base import BasePDU
from ..model.register import Register, HR, IR

_logger = logging.getLogger(__name__)


# The function codes that can appear in the 'func' field.

NULLRESPONSE = 0
READHOLDING = 3
READINPUT = 4
WRITEHOLDING = 6
READBATTERY = 22


# Each transparent message has a subset of these fields in the wire encoding.
# They always appear in this order, when present.
class Field(Flag):
    """Flags for optional fields"""
    SERIAL = auto()
    BASE = auto()
    COUNT = auto()
    VALUES = auto()


class TransparentMessage(BasePDU):
    """Root of the hierarchy for 2/Transparent PDUs."""

    function_code: ClassVar[int] = 2
    transparent_function_code: ClassVar[int]
    fields: ClassVar[Field]

    # This is provided for the convenience of the model.
    # Read(Battery)InputRegistersResponse sets this to IR,
    # ReadHoldingRegistersResponse sets it to HR.
    register_class: ClassVar[type[Register]]

    # This assists with choice of message class during decoding
    _pdu_lut: ClassVar[dict[int, type["TransparentMessage"]]]

    # These defaults are stored as class attributes, but will usually
    # be overridden as instance attributes
    # register_count is slightly different: NullResponse and WriteHoldingRegister*
    # override with their own class attributes
    base_register: int = -1
    register_count: int = -1
    register_values: list[int] = []
    slave_address: int = 0x32
    error: bool = False
    padding: int = 0x08
    check: int = -1

    def __init__(self, **kwargs):
        # simply copy all keys as attributes
        for att in kwargs:
            setattr(self, att, kwargs[att])

        # sanity-check that any required fields were supplied with valid values
        # (for instances both constructed directly and decoded from the wire).
        # If not, the invalid default values stored in the class will trigger errors.
        fields = self.fields
        if Field.BASE in fields and not 0 <= self.base_register <= 0xFFFF:
            raise InvalidPduState("base_register")
        if Field.COUNT in fields and not 1 <= self.register_count <= 60:
            raise InvalidPduState("register_count")
        if Field.VALUES in fields:
            values = self.register_values
            if not values or len(values) != self.register_count:
                raise InvalidPduState("register_values")

    def __str__(self) -> str:
        def format_kv(key, val):
            if val is None:
                val = "?"
            elif key == "slave_address":
                # if val == 0x32:
                #     return None
                val = f"0x{val:02x}"
            elif key == "register_count" and val == 60:
                return None
            # elif key in ('check', 'padding'):
            #     val = f'0x{val:04x}'
            # elif key == 'raw_frame':
            #     return f'raw_frame={len(val)}b'
            elif key == "nulls":
                return f"nulls=[0]*{len(val)}"
            elif key in (
                "inverter_serial_number",
                "data_adapter_serial_number",
                "error",
                "check",
                "padding",
                "register_values",
                "raw_frame",
                "_builder",
            ):
                return None
            return f"{key}={val}"

        args = []
        if self.error:
            args += ["ERROR"]
        args += [format_kv(k, v) for k, v in vars(self).items()]

        return (
            f"{self.function_code}:{getattr(self, 'transparent_function_code', '_')}/"
            f"{self.__class__.__name__}({' '.join([a for a in args if a is not None])})"
        )

    def _encode_function_data(self):
        """Add the wire-encoding of the payload"""

        # The crc is computed over a subset of the fields.
        # Add those to a second PayloadEncoder instance, so that
        # we can compute the crc, and then just append that whole
        # piece as a single component
        crc_builder = PayloadEncoder()

        self._builder.add_64bit_uint(self.padding)

        crc_builder.add_8bit_uint(self.slave_address)
        crc_builder.add_8bit_uint(self.transparent_function_code)
        if Field.SERIAL in self.fields:
            crc_builder.add_string(self.inverter_serial_number, 10)
        if Field.BASE in self.fields:
            crc_builder.add_16bit_uint(self.base_register)
        if Field.COUNT in self.fields:
            crc_builder.add_16bit_uint(self.register_count)
        if Field.VALUES in self.fields:
            for v in self.register_values:
                crc_builder.add_16bit_uint(v)
        crc = crc_builder.crc

        self._builder.append(crc_builder.payload)
        self._builder.add_16bit_le(crc)

    @classmethod
    def decode_main_function(cls, decoder: PayloadDecoder, **attrs) -> "BasePDU":
        """Decode transparent-specific part of the payload and create a suitable instance."""

        # On entry, cls is either TransparentRequest or TransparentResponse
        # These are just temporary classes until we identify the function code

        attrs["data_adapter_serial_number"] = decoder.decode_string(10)
        attrs["padding"] = decoder.decode_64bit_uint()
        attrs["slave_address"] = decoder.decode_8bit_uint()
        transparent_function_code = decoder.decode_8bit_uint()
        if transparent_function_code & 0x80:
            attrs["error"] = True
            transparent_function_code &= 0x7F

        # Now we can switch to the real class, and use the flags to
        # decode the variable part of the message
        cls = cls._pdu_lut[transparent_function_code]
        assert cls.transparent_function_code == transparent_function_code

        fields = cls.fields
        if Field.SERIAL in fields:
            attrs['inverter_serial_number'] = decoder.decode_string(10)
        if Field.BASE in fields:
            attrs['base_register'] = decoder.decode_16bit_uint()
        count = cls.register_count
        if Field.COUNT in fields:
            attrs['register_count'] = count = decoder.decode_16bit_uint()
        if Field.VALUES in fields:
            attrs['register_values'] = [
                decoder.decode_16bit_uint() for _ in range(count)
            ]

        attrs["check"] = decoder.decode_16bit_uint()

        return cls(**attrs)

    def shape_hash(self) -> int:
        """Calculates the "shape hash" for a given message.

        The shape hash is used for matching up requests and responses.
        By hashing on the interesting components of a message, we can
        decide whether an incoming response matches an outgoing request.
        Because values are omitted, a Request and its matching Response
        will have the same shape_hash value.
        """

        # just use a simple integer, with components scaled up to different
        # bit regions. Effectively bitfields, but decimal rather than binary
        # (so round ranges up to multiples of 10)
        #   slave_address is in range 0-999
        #   transparent function id is range 0-99
        #   register count is in range 0-99
        #   base register is at the top

        SCALE_ADDRESS = 1
        SCALE_FUNC = SCALE_ADDRESS * 1000
        SCALE_COUNT = SCALE_FUNC * 100
        SCALE_BASE = SCALE_COUNT * 100

        # All requests for which we might take the hash should have a base address.
        assert Field.BASE in self.fields

        # The register count is not explicit for a WriteHoldingRegisterRequest, but
        # we can get it from the class attribute, so no need to special case.

        return (
            self.slave_address * SCALE_ADDRESS
            + self.transparent_function_code * SCALE_FUNC
            + self.register_count * SCALE_COUNT
            + self.base_register * SCALE_BASE
        )


    # A helper for use by plant when processing ReadXXXRegistersResponse
    # Outputs pairs in exactly the format required by dict.update()
    def enumerate(self) -> Iterator[tuple[Register, int]]:
        """Generate pairs of (register, value) from the message."""
        assert Field.BASE in self.fields and Field.VALUES in self.fields
        idx = self.base_register
        cls = self.register_class
        for val in self.register_values:
            yield cls(idx), val
            idx += 1


# These serve two purposes:
# - they are markers in the class hierarchy to distinguish requests from
#   responses
# - they are placeholder classes for the decoding mechanism: they are
#   chosen as the initial decoding classes, until the transparent function
#   code is found, in which case they choose the real pdu class.
# Because we can't reference classes before they are defined, _pdu_lut is
# added at the bottom of the file.


class TransparentRequest(TransparentMessage):
    """Parent/decoder of request classes."""


class TransparentResponse(TransparentMessage):
    """Parent/decoder of response classes."""


# Now all the other classes are just trivial wrappers,
# supplying class variables to assist in encoding / decoding.


class ReadInputRegistersRequest(TransparentRequest):
    transparent_function_code = READINPUT
    fields = Field.BASE | Field.COUNT


class ReadInputRegistersResponse(TransparentResponse):
    transparent_function_code = READINPUT
    fields = Field.SERIAL | Field.BASE | Field.COUNT | Field.VALUES
    register_class = IR


class ReadBatteryInputRegistersRequest(TransparentRequest):
    transparent_function_code = READBATTERY
    fields = Field.BASE | Field.COUNT


class ReadBatteryInputRegistersResponse(TransparentResponse):
    transparent_function_code = READBATTERY
    fields = Field.SERIAL | Field.BASE | Field.COUNT | Field.VALUES
    register_class = IR


class ReadHoldingRegistersRequest(TransparentRequest):
    transparent_function_code = READHOLDING
    fields = Field.BASE | Field.COUNT


class ReadHoldingRegistersResponse(TransparentResponse):
    transparent_function_code = READHOLDING
    fields = Field.SERIAL | Field.BASE | Field.COUNT | Field.VALUES
    register_class = HR


# Internally we want WriteHoldingRegister* to use the same interface as the others,
# with a register_count of 1. But for convenience, allow 'register' as an alias for
# 'base_register', and 'value' as an alias for register_values[0]


class WriteHoldingRegisterRequest(TransparentRequest):
    transparent_function_code = WRITEHOLDING
    fields = Field.BASE | Field.VALUES
    register_count = 1

    # translate the aliases to the internal names
    # we need to delete the aliases to prevent super().__init__()
    # from attempting to setattr() (since they are implemented as properties)

    def __init__(self, **kwargs):
        if 'register' in kwargs:
            kwargs['base_register'] = kwargs['register']
            del kwargs['register']
        if 'value' in kwargs:
            kwargs['register_values'] = [kwargs['value']]
            del kwargs['value']
        if 'register_count' in kwargs:
            raise InvalidPduState("Unexpected register_count parameter")
        super().__init__(**kwargs)


class WriteHoldingRegisterResponse(TransparentResponse):
    transparent_function_code = WRITEHOLDING
    fields = Field.SERIAL | Field.BASE | Field.VALUES
    register_count = 1
    register_class = HR

    @property
    def register(self):
        return self.base_register

    @property
    def value(self):
        return self.register_values[0]


# The NullResponse seems to be a quirk of the GivEnergy implementation – from time to time
# these responses will be sent unprompted by the remote device and this just handles it
# gracefully and allows further debugging. The function data payload seems to be invariably
# just a series of nulls.


class NullResponse(TransparentMessage):
    transparent_function_code = NULLRESPONSE
    fields = Field.SERIAL | Field.VALUES
    register_count = 62


# Now that all the classes are defined, we can poke in the decoding luts.
TransparentRequest._pdu_lut = {
    READHOLDING: ReadHoldingRegistersRequest,
    READINPUT: ReadInputRegistersRequest,
    WRITEHOLDING: WriteHoldingRegisterRequest,
    READBATTERY: ReadBatteryInputRegistersRequest,
}

TransparentResponse._pdu_lut = {
    NULLRESPONSE: NullResponse,
    READHOLDING: ReadHoldingRegistersResponse,
    READINPUT: ReadInputRegistersResponse,
    WRITEHOLDING: WriteHoldingRegisterResponse,
    READBATTERY: ReadBatteryInputRegistersResponse,
}
