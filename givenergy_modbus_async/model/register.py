"""
Helper classes for the Plant, Inverter and Battery.

Applications shouldn't need to worry about these.
"""

from dataclasses import dataclass
from datetime import datetime
from json import JSONEncoder
import math
from textwrap import dedent
from typing import Any, Callable, Optional, Union

from ..exceptions import (
    ConversionError,
)

from . import TimeSlot


class Converter:
    """Type of data register represents. Encoding is always big-endian."""

    @staticmethod
    def uint16(val: int) -> int:
        """Simply return the raw unsigned 16-bit integer register value."""
        if val is not None:
            return int(val)

    @staticmethod
    def int16(val: int) -> int:
        """Interpret as a 16-bit integer register value."""
        if val is not None:
            if val & (1 << (16 - 1)):
                val -= 1 << 16
            return val

    @staticmethod
    def duint8(val: int, *idx: int) -> int:
        """Split one register into two unsigned 8-bit ints and return the specified index."""
        if val is not None:
            vals = (val >> 8), (val & 0xFF)
            return vals[idx[0]]

    @staticmethod
    def uint32(high_val: int, low_val: int) -> int:
        """Combine two registers into an unsigned 32-bit int."""
        if high_val is not None and low_val is not None:
            return (high_val << 16) + low_val
        
    def bitfield(val: int, low: int, high: int) -> int:
        """Return int of binary string from range requested in input as binary string"""
        res=int(format(val,'016b')[low:high+1],2)
        return res

    @staticmethod
    def timeslot(start_time: int, end_time: int) -> TimeSlot:
        """Interpret register as a time slot."""
        if start_time is not None and end_time is not None:
            return TimeSlot.from_repr(start_time, end_time)   

    @staticmethod
    def bool(val: int) -> bool:
        """Interpret register as a bool."""
        if val is not None:
            return bool(val)
        return None

    @staticmethod
    def string(*vals: int) -> Optional[str]:
        """Represent one or more registers as a concatenated string."""
        if vals is not None and None not in vals:
            return (
                b"".join(v.to_bytes(2, byteorder="big") for v in vals)
                .decode(encoding="latin1")
                .replace("\x00", "")
                .upper()
            )
        return None

    @staticmethod
    def fstr(val, fmt) -> Optional[str]:
        """Render a value using a format string."""
        if val is not None:
            return f"{val:{fmt}}"
        return None

    @staticmethod
    def firmware_version(dsp_version: int, arm_version: int) -> Optional[str]:
        """Represent ARM & DSP firmware versions in the same format as the dashboard."""
        if dsp_version is not None and arm_version is not None:
            return f"D0.{dsp_version}-A0.{arm_version}"

    @staticmethod
    def gateway_version(first: int,second: int,third: int,fourth: int,) -> Optional[str]:
        """Return Gateway software ID."""
        gwversion=bytearray.fromhex(hex(first)[2:]).decode()+bytearray.fromhex(hex(second)[2:]).decode()+str(third).zfill(2)+str(fourth).zfill(2)
        return gwversion

    @staticmethod
    def inverter_max_power(device_type_code: str) -> Optional[int]:
        """Determine max inverter power from device_type_code."""
        dtc_to_power = {
            "2001": 5000,
            "2002": 4600,
            "2003": 3600,
            "3001": 3000,
            "3002": 3600,
            "4001": 6000,
            "4002": 8000,
            "4003": 10000,
            "4004": 11000,
            "5001": 5000,
            "8001": 6000,
        }
        return dtc_to_power.get(device_type_code)
    
    @staticmethod
    def nominal_frequency(option: int) -> Optional[int]:
        """Determine max inverter power from device_type_code."""
        frequency = [50,60]
        return frequency[option]
    
    @staticmethod
    def nominal_voltage(option: int) -> Optional[int]:
        """Determine max inverter power from device_type_code."""
        voltage = [230,208,240]
        return voltage[option]

    @staticmethod
    def hex(val: int, width: int = 4) -> str:
        """Represent a register value as a 4-character hex string."""
        if val is not None:
            return f"{val:0{width}x}"

    @staticmethod
    def milli(val: int) -> float:
        """Represent a register value as a float in 1/1000 units."""
        if val is not None:
            return val / 1000

    @staticmethod
    def centi(val: int) -> float:
        """Represent a register value as a float in 1/100 units."""
        if val is not None:
            return val / 100

    @staticmethod
    def deci(val: int) -> float:
        """Represent a register value as a float in 1/10 units."""
        if val is not None:
            return val / 10

    @staticmethod
    def datetime(year, month, day, hour, min, sec) -> Optional[datetime]:
        """Compose a datetime from 6 registers."""
        if 0>year>999: year=0 #try to get rid of the spurious year error
        if 0>month>12: month=0 #try to get rid of the spurious year error
        if 0>day>31: day=1
        if 0>hour>23: hour=0 #try to get rid of the spurious hour error
        if 0>min>60: min=0 #try to get rid of the spurious hour error
        if 0>sec>60: sec=0 #try to get rid of the spurious hour error
        if None not in [year, month, day, hour, min, sec]:
            return datetime(year + 2000, month, day, hour, min, sec)
        return None


@dataclass(init=False)
class RegisterDefinition:
    """Specifies how to convert raw register values into their actual representation."""

    pre_conv: Union[Callable, tuple, None]
    post_conv: Union[Callable, tuple[Callable, Any], None]
    registers: tuple["Register"]
    valid: Optional[tuple[int, int]]

    def __init__(self, *args, valid=None):
        self.pre_conv = args[0]
        self.post_conv = args[1]
        self.registers = args[2:]  # type: ignore[assignment]
        self.valid = valid
        # only single-register attributes are writable
        assert valid is None or len(self.registers) == 1

    def __hash__(self):
        return hash(self.registers)



# This is used as the metaclass for Inverter and Battery,
# in order to dynamically generate a docstring from the
# register definitions.

class DynamicDoc(type):
    """A metaclass for generating dynamic __doc__ string.

    A class using this metaclass must implement a class method
    _gendoc() which will be invoked by any access to cls.__doc__
    (typically documentation tools like pydoc).
    """

    @property
    def __doc__(self):
        """Invoke a helper to generate class docstring."""
        return self._gendoc()


class RegisterGetter:
    """
    Specifies how device attributes are derived from raw register values.
    
    This is the base class for Inverter and Battery, and provides the common
    code for constructing python attrbitutes from the register definitions.
    """

    # defined by subclass
    REGISTER_LUT: dict[str, RegisterDefinition]
    _DOC: str

    # TODO: cache is actually a RegisterCache, but importing that gives a circular dependency
    def __init__(self, cache: Any):
        self.cache = cache  # RegisterCache

    # this implements the magic of providing attributes based
    # on the register lut
    def __getattr__(self, name: str):
        return self.get(name)

    # or you can just use inverter.get('name')
    def get(self, key: str) -> Any:
        """Return a named register's value, after pre- and post-conversion."""
        r = self.REGISTER_LUT[key]

        regs = [self.cache.get(r) for r in r.registers]

        if None in regs:
            return None

        try:
            if r.pre_conv:
                if isinstance(r.pre_conv, tuple):
                    args = regs + list(r.pre_conv[1:])
                    val = r.pre_conv[0](*args)
                else:
                    val = r.pre_conv(*regs)
            else:
                val = regs

            if r.post_conv:
                if isinstance(r.post_conv, tuple):
                    return r.post_conv[0](val, *r.post_conv[1:])
                else:
                    if not isinstance(r.post_conv, Callable):
                        pass
                    return r.post_conv(val)
            return val
        except ValueError as err:
            raise ConversionError(key, regs, str(err)) from err

    # This gets invoked during pydoc or similar by a bit of python voodoo.
    # Inverter and Battery use util.DynamicDoc as a metaclass, and
    # that defines __doc__ as a property which ends up in here.
    @classmethod
    def _gendoc(cls):
        """"Construct a docstring from fixed prefix and register list."""

        doc = cls._DOC + dedent(
        """

        The following list of attributes was automatically generated from the
        register definition list. They are fabricated at runtime via ``__getattr__``.
        Note that the actual set of registers available depends on the inverter
        model - accessing a register that doesn't exist will return ``None``.

        Because these attributes are not listed in ``__dict__`` they may not be
        visible to all python tools.
        Some appear multiple times as aliases.\n\n"""
        )

        for reg in cls.REGISTER_LUT.keys():
            doc += '* ' + reg + "\n"
        return doc


class RegisterEncoder(JSONEncoder):
    """Custom JSONEncoder to work around Register behaviour.

    This is a workaround to force registers to render themselves as strings instead of
    relying on the internal identity by default.
    """

    def default(self, o: Any) -> str:
        """Custom JSON encoder to treat RegisterCaches specially."""
        if isinstance(o, Register):
            return f"{o._type}_{o._idx}"
        else:
            return super().default(o)


class Register:
    """Register base class."""

    TYPE_HOLDING = "HR"
    TYPE_INPUT = "IR"

    _type: str
    _idx: int

    def __init__(self, idx):
        self._idx = idx

    def __str__(self):
        return "%s_%d" % (self._type, int(self._idx))

    __repr__ = __str__

    def __eq__(self, other):
        return (
            isinstance(other, Register)
            and self._type == other._type
            and self._idx == other._idx
        )

    def __hash__(self):
        return hash((self._type, self._idx))


class HR(Register):
    """Holding Register."""

    _type = Register.TYPE_HOLDING


class IR(Register):
    """Input Register."""

    _type = Register.TYPE_INPUT
