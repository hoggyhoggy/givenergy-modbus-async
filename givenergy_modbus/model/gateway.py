"""
High level interpretation of the gateway modbus registers.

The Gateway itself is the primary class; the others are
supporting enumerations.
"""

from typing import Optional
from .baseinverter import BaseInverter
from .register import *
from .register import (
    Converter as C,
    DynamicDoc,
    HR,
    IR,
    RegisterDefinition as Def,
    RegisterGetter,
)


class Gateway(RegisterGetter, metaclass=DynamicDoc):
    # pylint: disable=missing-class-docstring
    # The metaclass turns accesses to __doc__ into calls to
    # _gendoc()  (which we inherit from RegisterGetter)

    _DOC = """Interprets the low-level registers in the gateway as named attributes."""

    # TODO: add register aliases and valid=(min,max) for writable registers
    NEW_LUT = {
        #
        # Input Registers, block 1600-1640
        #
        "software_version": Def(C.gateway_version, None, IR(1600),IR(1601),IR(1602),IR(1603)),
        "work_mode": Def(C.uint16, None, IR(1604)),
        #"system_enable": Def(C.uint16, None, IR(1605)),
        #"do_state": Def(C.string, None, IR(1606)),
        #"di_state": Def(C.string, None, IR(1607)),
        "v_grid": Def(C.int16, C.deci, IR(1608)),
        "i_grid": Def(C.int16, C.deci, IR(1609)),
        "v_load": Def(C.deci, None, IR(1610)),
        "i_load": Def(C.deci, None, IR(1611)),
        "i_inverter": Def(C.int16, C.deci, IR(1612)),
        "p_ac1": Def(C.int16, None, IR(1616)),
        "p_pv": Def(C.uint16, None, IR(1617)),
        "p_load": Def(C.uint16, None, IR(1618)),
        "p_liberty": Def(C.int16, None, IR(1619)),
        "fault_protection": Def(C.uint32, None, IR(1620),IR(1621)),
        "gateway_fault_codes": Def(C.uint32, C.gateway_fault_code, IR(1622),IR(1623)),
        "v_grid_relay": Def(C.deci, None, IR(1624)),
        "v_inverter_relay": Def(C.deci, None, IR(1625)),
        "first_inverter_serial_number": Def(C.string, None, IR(1627),IR(1628),IR(1629),IR(1630),IR(1631)),
        "e_grid_import_today": Def(C.deci, None, IR(1640)),
        "e_grid_import_total": Def(C.uint32, C.deci, IR(1641),IR(1642)),
        "e_pv_today": Def(C.deci, None, IR(1643)),
        "e_pv_total": Def(C.uint32, C.deci, IR(1644),IR(1645)),
        "e_grid_export_today": Def(C.deci, None, IR(1646)),
        "e_grid_export_total": Def(C.uint32, C.deci, IR(1647),IR(1648)),
        "e_load_today": Def(C.deci, None, IR(1655)),
        "e_load_total": Def(C.uint32, C.deci, IR(1656),IR(1657)),
    ## BATTERY / AIO Total?
        "e_aio_charge_today": Def(C.deci, None, IR(1649)),
        "e_aio_charge_total": Def(C.uint32, C.deci, IR(1650),IR(1651)),
        "e_aio_discharge_today": Def(C.deci, None, IR(1652)),
        "e_aio_discharge_total": Def(C.uint32, C.deci, IR(1653),IR(1654)),
        "p_aio_total": Def(C.int16, None, IR(1702)),
        "aio_state": Def(C.uint16, State, IR(1703)),
        "battery_firmware_version": Def(C.int16, None, IR(1704)),
    ## AIO - 1
        "e_aio1_charge_today": Def(C.deci, None, IR(1705)),
        "e_aio1_charge_total": Def(C.uint32, C.deci, IR(1706),IR(1707)),
        "e_aio1_discharge_today": Def(C.deci, None, IR(1750)),
        "e_aio1_discharge_total": Def(C.uint32, C.deci, IR(1751),IR(1752)),
        "aio1_soc": Def(C.uint16, None, IR(1801)),
        "p_aio1_inverter": Def(C.int16, None, IR(1816)),
        "aio1_serial_number": Def(C.string, None, IR(1831), IR(1832), IR(1833), IR(1834), IR(1835)),
    ## AIO - 2
        "e_aio2_charge_today": Def(C.deci, None, IR(1708)),
        "e_aio2_charge_total": Def(C.uint32, C.deci, IR(1709),IR(1710)),
        "e_aio2_discharge_today": Def(C.deci, None, IR(1753)),
        "e_aio2_discharge_total": Def(C.uint32, C.deci, IR(1754),IR(1755)),
        "aio2_soc": Def(C.uint16, None, IR(1802)),
        "p_aio2_inverter": Def(C.int16, None, IR(1817)),
        "aio2_serial_number": Def(C.string, None, IR(1838), IR(1839), IR(1840), IR(1841), IR(1842)),
    ## AIO - 3
        "e_aio3_charge_today": Def(C.deci, None, IR(1711)),
        "e_aio3_charge_total": Def(C.uint32, C.deci, IR(1712),IR(1713)),
        "e_aio3_discharge_today": Def(C.deci, None, IR(1756)),
        "e_aio3_discharge_total": Def(C.uint32, C.deci, IR(1757),IR(1758)),
        "aio3_soc": Def(C.uint16, None, IR(1803)),
        "p_aio3_inverter": Def(C.int16, None, IR(1818)),
        "aio3_serial_number": Def(C.string, None, IR(1845), IR(1846), IR(1847), IR(1848), IR(1849)),

        "parallel_aio_num": Def(C.uint16, None, IR(1700)),
        "parallel_aio_online_num": Def(C.uint16, None, IR(1701)),


    ## Battery
        "e_battery_charge_today": Def(C.deci, None, IR(1795)),
        "e_battery_charge_total": Def(C.uint32, C.deci, IR(1796),IR(1797)),
        "e_battery_discharge_today": Def(C.deci, None, IR(1798)),
        "e_battery_discharge_total": Def(C.uint32, C.deci, IR(1799),IR(1800)),
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