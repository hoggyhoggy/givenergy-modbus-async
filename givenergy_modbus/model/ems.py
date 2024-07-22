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


class EMS(RegisterGetter, metaclass=DynamicDoc):
    # pylint: disable=missing-class-docstring
    # The metaclass turns accesses to __doc__ into calls to
    # _gendoc()  (which we inherit from RegisterGetter)

    _DOC = """Interprets the low-level registers in the inverter as named attributes."""

    # TODO: add register aliases and valid=(min,max) for writable registers


    NEW_LUT = {
        #
        # Holding Registers 2040-2075
        #
        "plant_status": Def(C.uint16, Status, HR(2040)),
        "expected_inverter_count": Def(C.uint16, None, HR(2041)),
        "expected_meter_count": Def(C.uint16, None, HR(2042)),
        "expected_car_charger_count": Def(C.uint16, None, HR(2043)),
        "discharge_slot_1": Def(C.timeslot, None, HR(2044), HR(2045)),
        "discharge_slot_1_start": Def(C.uint16, None, HR(2044), valid=(0,2359)),
        "discharge_slot_1_end": Def(C.uint16, None, HR(2045), valid=(0,2359)),
        "discharge_target_1": Def(C.uint16, None, HR(2046), valid=(4,100)),
        "discharge_slot_2": Def(C.timeslot, None, HR(2047), HR(2048)),
        "discharge_slot_2_start": Def(C.uint16, None, HR(2047), valid=(0,2359)),
        "discharge_slot_2_end": Def(C.uint16, None, HR(2048), valid=(0,2359)),
        "discharge_target_2": Def(C.uint16, None, HR(2049), valid=(4,100)),
        "discharge_slot_3": Def(C.timeslot, None, HR(2050), HR(2051)),
        "discharge_slot_3_start": Def(C.uint16, None, HR(2050), valid=(0,2359)),
        "discharge_slot_3_end": Def(C.uint16, None, HR(2051), valid=(0,2359)),
        "discharge_target_3": Def(C.uint16, None, HR(2052), valid=(4,100)),
        "charge_slot_1": Def(C.timeslot, None, HR(2053), HR(2054)),
        "charge_slot_1_start": Def(C.uint16, None, HR(2053), valid=(0,2359)),
        "charge_slot_1_end": Def(C.uint16, None, HR(2054), valid=(0,2359)),
        "charge_target_1": Def(C.uint16, None, HR(2055), valid=(4,100)),
        "charge_slot_2": Def(C.timeslot, None, HR(2056), HR(2057)),
        "charge_slot_2_start": Def(C.uint16, None, HR(2056), valid=(0,2359)),
        "charge_slot_2_end": Def(C.uint16, None, HR(2057), valid=(0,2359)),
        "charge_target_2": Def(C.uint16, None, HR(2058), valid=(4,100)),
        "charge_slot_3": Def(C.timeslot, None, HR(2059), HR(2060)),
        "charge_slot_3_start": Def(C.uint16, None, HR(2059), valid=(0,2359)),
        "charge_slot_3_end": Def(C.uint16, None, HR(2060), valid=(0,2359)),
        "charge_target_3": Def(C.uint16, None, HR(2061), valid=(4,100)),
        "export_slot_1": Def(C.timeslot, None, HR(2062), HR(2063)),
        "export_slot_1_start": Def(C.uint16, None, HR(2062), valid=(0,2359)),
        "export_slot_1_end": Def(C.uint16, None, HR(2063), valid=(0,2359)),
        "export_target_1": Def(C.uint16, None, HR(2064), valid=(4,100)),
        "export_slot_2": Def(C.timeslot, None, HR(2065), HR(2066)),
        "export_slot_2_start": Def(C.uint16, None, HR(2065), valid=(0,2359)),
        "export_slot_2_end": Def(C.uint16, None, HR(2066), valid=(0,2359)),
        "export_target_2": Def(C.uint16, None, HR(2067), valid=(4,100)),
        "export_slot_3": Def(C.timeslot, None, HR(2068), HR(2069)),
        "export_slot_3_start": Def(C.uint16, None, HR(2068), valid=(0,2359)),
        "export_slot_3_end": Def(C.uint16, None, HR(2069), valid=(0,2359)),
        "export_target_3": Def(C.uint16, None, HR(2070), valid=(4,100)),
        "export_power_limit": Def(C.uint16, None, HR(2071)),
        "car_charge_mode": Def(C.uint16, None, HR(2072), valid=(0,3)),
        "car_charge_boost": Def(C.uint16, None, HR(2073), valid=(0,22000)),
        "plant_charge_compensation": Def(C.uint16, None, HR(2074), valid=(-5,5)),
        "plant_discharge_compensation": Def(C.uint16, None, HR(2075), valid=(-5,5)),
        #
        # Input Registers, block 0-59
        #
        "status": Def(C.uint16, Status, IR(0)),
        "p_active_grid": Def(C.deci, None, IR(4)),
        "e_inverter_out_total": Def(C.uint32, C.deci, IR(6), IR(7)),
        "e_active_generation_total": Def(C.uint16, None, IR(18)),
        "e_grid_out_total": Def(C.uint32, C.deci, IR(21), IR(22)),
        "e_grid_out_day": Def(C.deci, None, IR(25)),
        "e_grid_in_day": Def(C.deci, None, IR(26)),
        "e_inverter_in_total": Def(C.uint32, C.deci, IR(27), IR(28)),
        "p_grid_active": Def(C.int16, None, IR(30)),
        "e_grid_in_total": Def(C.uint32, C.deci, IR(32), IR(33)),
        "e_inverter_in_day": Def(C.deci, None, IR(35)),
        "e_inverter_out_today": Def(C.deci, None, IR(37)),
        "p_load_demand": Def(C.uint16, None, IR(42)),
        "e_generation_day": Def(C.deci, None, IR(44)),
        "e_generation_total": Def(C.uint32, C.deci, IR(45), IR(46)),
        "work_time_total": Def(C.uint32, None, IR(47), IR(48)),
        "p_inverter_active": Def(C.int16, None, IR(52)),
        
        #
        # Input Registers, block 2040-2095
        # EMS Plant info
        #

        "ems_status": Def(C.uint16, Status, IR(2040)),
        "meter_count": Def(C.uint16, None, IR(2041)),
        "meter_types": Def(C.uint16, None, IR(2042)),   #needs type
        "meter_1_status": Def(C.bitfield, MeterStatus, IR(2043),0,1),
        "meter_2_status": Def(C.bitfield, MeterStatus, IR(2043),2,3),
        "meter_3_status": Def(C.bitfield, MeterStatus, IR(2043),4,5),
        "meter_4_status": Def(C.bitfield, MeterStatus, IR(2043),6,7),
        "meter_5_status": Def(C.bitfield, MeterStatus, IR(2043),8,9),
        "meter_6_status": Def(C.bitfield, MeterStatus, IR(2043),10,11),
        "meter_7_status": Def(C.bitfield, MeterStatus, IR(2043),12,13),
        "meter_8_status": Def(C.bitfield, MeterStatus, IR(2043),14,15),
        "inverter_count": Def(C.uint16, None, IR(2044)),
        "inverter_1_status": Def(C.bitfield, Status, IR(2045),0,2),
        "inverter_2_status": Def(C.bitfield, Status, IR(2045),3,5),
        "inverter_3_status": Def(C.bitfield, Status, IR(2045),6,8),
        "inverter_4_status": Def(C.bitfield, Status, IR(2045),9,11),
        "meter_1_power": Def(C.int16, None, IR(2046)),
        "meter_2_power": Def(C.int16, None, IR(2047)),
        "meter_3_power": Def(C.int16, None, IR(2048)),
        "meter_4_power": Def(C.int16, None, IR(2049)),
        "meter_5_power": Def(C.int16, None, IR(2050)),
        "meter_6_power": Def(C.int16, None, IR(2051)),
        "meter_7_power": Def(C.int16, None, IR(2052)),
        "meter_8_power": Def(C.int16, None, IR(2053)),
        "inverter_1_power": Def(C.int16, None, IR(2054)),
        "inverter_2_power": Def(C.int16, None, IR(2055)),
        "inverter_3_power": Def(C.int16, None, IR(2056)),
        "inverter_4_power": Def(C.int16, None, IR(2057)),
        "inverter_1_soc": Def(C.uint16, None, IR(2058)),
        "inverter_2_soc": Def(C.uint16, None, IR(2059)),
        "inverter_3_soc": Def(C.uint16, None, IR(2060)),
        "inverter_4_soc": Def(C.uint16, None, IR(2061)),
        "inverter_1_temp": Def(C.int16, C.deci, IR(2062)),
        "inverter_2_temp": Def(C.int16, C.deci, IR(2063)),
        "inverter_3_temp": Def(C.int16, C.deci, IR(2064)),
        "inverter_4_temp": Def(C.int16, C.deci, IR(2065)),
        "inverter_1_serial_number": Def(C.string, None, IR(2066), IR(2067), IR(2068), IR(2069), IR(2070)),
        "inverter_2_serial_number": Def(C.string, None, IR(2071), IR(2072), IR(2073), IR(2074), IR(2075)),
        "inverter_3_serial_number": Def(C.string, None, IR(2076), IR(2077), IR(2078), IR(2079), IR(2080)),
        "inverter_4_serial_number": Def(C.string, None, IR(2081), IR(2082), IR(2083), IR(2084), IR(2085)),
        "calc_load_power": Def(C.uint16, None, IR(2086)),
        "measured_load_power": Def(C.uint16, None, IR(2087)),
        "total_generation_load_power": Def(C.uint16, None, IR(2088)),
        "grid_meter_power": Def(C.int16, None, IR(2089)),
        "total_battery_power": Def(C.int16, None, IR(2090)),
        "remaining_battery_wh": Def(C.uint16, None, IR(2091)),
        "other_battery_power": Def(C.int16, None, IR(2094)),
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

