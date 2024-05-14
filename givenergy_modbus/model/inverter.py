"""
High level interpretation of the inverter modbus registers.

The Inverter itself is the primary class; the others are
supporting enumerations.
"""

from .register import *
from .baseinverter import BaseInverter
from typing import Optional
from .register import (
    Converter as C,
    DynamicDoc,
    HR,
    IR,
    RegisterDefinition as Def,
    RegisterGetter,
)

class Inverter(RegisterGetter, metaclass=DynamicDoc):
    # pylint: disable=missing-class-docstring
    # The metaclass turns accesses to __doc__ into calls to
    # _gendoc()  (which we inherit from RegisterGetter)

    _DOC = """Interprets the low-level registers in the inverter as named attributes."""

    # TODO: add register aliases and valid=(min,max) for writable registers

    
    NEW_LUT = {
        #
        # Holding Registers, block 4080-4139
        #
        "pv_power_setting": Def(C.uint32, None, HR(4107), HR(4108)),
        "e_battery_discharge_total3": Def(C.uint32, None, HR(4109), HR(4110)),
        "e_battery_charge_total3": Def(C.uint32, None, HR(4111), HR(4112)),
        "e_battery_discharge_today3": Def(C.uint16, None, HR(4113)),
        "e_battery_charge_today3": Def(C.uint16, None, HR(4114)),
        #
        # Holding Registers, block 4140-4199
        #
        "e_inverter_export_total": Def(C.uint32, None, HR(4141), HR(4142)),
    }
    REGISTER_LUT=dict(BaseInverter.REGISTER_LUT, **NEW_LUT)


    @classmethod
    def lookup_writable_register(cls, name: str, value: Optional[int] = None):
        """
        If the named register is writable and value is in range, return index.
        """

        regdef = cls.REGISTER_LUT[name]
        if regdef.valid is None:
            raise ValueError(f'{name} is not writable')
        if len(regdef.registers) > 1:
            raise NotImplementedError('wide register')

        if value is not None:
            if value < regdef.valid[0] or value > regdef.valid[1]:
                raise ValueError(f'{value} out of range for {name}')

            if regdef.valid[1] == 2359:
                # As a special case, assume this register is a time
                if value % 100 >= 60:
                    raise ValueError(f'{value} is not a valid time')

        return regdef.registers[0]._idx  # pylint: disable=protected-access
