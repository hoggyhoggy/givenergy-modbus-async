"""
High level interpretation of the inverter modbus registers.

The Inverter itself is the primary class; the others are
supporting enumerations.
"""

from enum import IntEnum, StrEnum
import math
from typing import Optional
from .register import (
    Converter as C,
    DynamicDoc,
    HR,
    IR,
    RegisterDefinition as Def,
    RegisterGetter,
)

class MeterType(IntEnum):
    """Installed meter type."""

    CT_OR_EM418 = 0
    EM115 = 1

    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)

class Generation(StrEnum):
    """Known Generations"""

    GEN1 = "Gen 1"
    GEN2 = "Gen 2"
    GEN3 = "Gen 3"

    @classmethod
    def _missing_(cls, value: int):
        """Pick generation from the arm_firmware_version."""
        arm_firmware_version_to_gen = {
            3: cls.GEN3,
            8: cls.GEN2,
            9: cls.GEN2,
        }
        key = math.floor(int(value) / 100)
        if gen := arm_firmware_version_to_gen.get(key):
            return gen
        else:
            return cls.GEN1

class Model(StrEnum):
    """Known models of inverters."""

    HYBRID = "2"
    AC = "3"
    HYBRID_3PH = "4"
    AC_3PH = "6"
    EMS = "5"
    GATEWAY = "7"
    ALL_IN_ONE = "8"

    @classmethod
    def _missing_(cls, value):
        """Pick model from the first digit of the device type code."""
        return cls(value[0])

class Status(IntEnum):
    """Inverter status."""

    WAITING = 0
    NORMAL = 1
    WARNING = 2
    FAULT = 3
    FLASHING_FIRMWARE_UPDATE = 4
    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)

class MeterStatus(IntEnum):
    DISABLED = 0
    ONLINE = 1
    OFFLINE = 2
    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)


class BatteryPauseMode(IntEnum):
    """Battery pause mode."""

    DISABLED = 0
    PAUSE_CHARGE = 1
    PAUSE_DISCHARGE = 2
    PAUSE_BOTH = 3

    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)

class BatteryType(IntEnum):
    """Installed battery type."""

    LEAD_ACID = 0
    LITHIUM = 1
    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)

class PowerFactorFunctionModel(IntEnum):
    """Power Factor function model."""

    PF_1 = 0
    PF_BY_SET = 1
    DEFAULT_PF_LINE = 2
    USER_PF_LINE = 3
    UNDER_EXCITED_INDUCTIVE_REACTIVE_POWER = 4
    OVER_EXCITED_CAPACITIVE_REACTIVE_POWER = 5
    QV_MODEL = 6

class UsbDevice(IntEnum):
    """USB devices that can be inserted into inverters."""

    NONE = 0
    WIFI = 1
    DISK = 2


class BatteryPowerMode(IntEnum):
    """Battery discharge strategy."""

    EXPORT = 0
    SELF_CONSUMPTION = 1

    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)

class BatteryCalibrationStage(IntEnum):
    """Battery calibration stages."""

    OFF = 0
    DISCHARGE = 1
    SET_LOWER_LIMIT = 2
    CHARGE = 3
    SET_UPPER_LIMIT = 4
    BALANCE = 5
    SET_FULL_CAPACITY = 6
    FINISH = 7

    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)

class EMS(RegisterGetter, metaclass=DynamicDoc):
    # pylint: disable=missing-class-docstring
    # The metaclass turns accesses to __doc__ into calls to
    # _gendoc()  (which we inherit from RegisterGetter)

    _DOC = """Interprets the low-level registers in the inverter as named attributes."""

    # TODO: add register aliases and valid=(min,max) for writable registers


    REGISTER_LUT = {
        #
        # Holding Registers, block 0-59
        #
        "device_type_code": Def(C.hex, None, HR(0)),
        "inverter_max_power": Def(C.hex, C.inverter_max_power, HR(0)),
        "model": Def(C.hex, Model, HR(0)),
        "module": Def(C.uint32, (C.hex, 8), HR(1), HR(2)),
        "num_mppt": Def((C.duint8, 0), None, HR(3)),
        "num_phases": Def((C.duint8, 1), None, HR(3)),
        # HR(4-6) unused
        "enable_ammeter": Def(C.bool, None, HR(7)),
        "first_battery_serial_number": Def(
            C.string, None, HR(8), HR(9), HR(10), HR(11), HR(12)
        ),
        "serial_number": Def(C.string, None, HR(13), HR(14), HR(15), HR(16), HR(17)),
        "first_battery_bms_firmware_version": Def(C.uint16, None, HR(18)),
        "dsp_firmware_version": Def(C.uint16, None, HR(19)),
        "enable_charge_target": Def(C.bool, None, HR(20), valid=(0, 1)),
        "arm_firmware_version": Def(C.uint16, None, HR(21)),
        "generation": Def(C.uint16, Generation, HR(21)),
        "firmware_version": Def(C.firmware_version, None, HR(19), HR(21)),
        "usb_device_inserted": Def(C.uint16, UsbDevice, HR(22)),
        "select_arm_chip": Def(C.bool, None, HR(23)),
        "variable_address": Def(C.uint16, None, HR(24)),
        "variable_value": Def(C.uint16, None, HR(25)),
        "grid_port_max_power_output": Def(C.uint16, None, HR(26)),
        "battery_power_mode": Def(C.uint16, BatteryPowerMode, HR(27), valid=(0, 1)),
        "enable_60hz_freq_mode": Def(C.bool, None, HR(28)),
        "soc_force_adjust": Def(C.uint16, BatteryCalibrationStage, HR(29)),
        "modbus_address": Def(C.uint16, None, HR(30)),
        "charge_slot_2": Def(C.timeslot, None, HR(31), HR(32)),
        "charge_slot_2_start": Def(C.uint16, None, HR(31), valid=(0, 2359)),
        "charge_slot_2_end": Def(C.uint16, None, HR(32), valid=(0, 2359)),
        "user_code": Def(C.uint16, None, HR(33)),
        "modbus_version": Def(C.centi, (C.fstr, "0.2f"), HR(34)),
        "system_time": Def(
            C.datetime, None, HR(35), HR(36), HR(37), HR(38), HR(39), HR(40)
        ),
        "enable_drm_rj45_port": Def(C.bool, None, HR(41)),
        "enable_reversed_ct_clamp": Def(C.bool, None, HR(42)),
        "charge_soc": Def((C.duint8, 0), None, HR(43)),
        "discharge_soc": Def((C.duint8, 1), None, HR(43)),
        "discharge_slot_2": Def(C.timeslot, None, HR(44), HR(45)),
        "discharge_slot_2_start": Def(C.uint16, None, HR(44), valid=(0, 2359)),
        "discharge_slot_2_end": Def(C.uint16, None, HR(45), valid=(0, 2359)),
        "bms_firmware_version": Def(C.uint16, None, HR(46)),
        "meter_type": Def(C.uint16, MeterType, HR(47)),
        "enable_reversed_115_meter": Def(C.bool, None, HR(48)),
        "enable_reversed_418_meter": Def(C.bool, None, HR(49)),
        "active_power_rate": Def(C.uint16, None, HR(50)),
        "reactive_power_rate": Def(C.uint16, None, HR(51)),
        "power_factor": Def(C.uint16, None, HR(52)),  # /10_000 - 1
        "enable_inverter_auto_restart": Def((C.duint8, 0), C.bool, HR(53)),
        "enable_inverter": Def((C.duint8, 1), C.bool, HR(53)),
        "battery_type": Def(C.uint16, BatteryType, HR(54)),
        "battery_nominal_capacity": Def(C.uint16, None, HR(55)),
        "discharge_slot_1": Def(C.timeslot, None, HR(56), HR(57)),
        "discharge_slot_1_start": Def(C.uint16, None, HR(56), valid=(0, 2359)),
        "discharge_slot_1_end": Def(C.uint16, None, HR(57), valid=(0, 2359)),
        "enable_auto_judge_battery_type": Def(C.bool, None, HR(58)),
        "enable_discharge": Def(C.bool, None, HR(59)),
        #
        # Holding Registers, block 60-119
        #
        "v_pv_start": Def(C.uint16, C.deci, HR(60)),
        "start_countdown_timer": Def(C.uint16, None, HR(61)),
        "restart_delay_time": Def(C.uint16, None, HR(62)),
        # skip protection settings HR(63-93)
        "charge_slot_1": Def(C.timeslot, None, HR(94), HR(95)),
        "charge_slot_1_start": Def(C.uint16, None, HR(94), valid=(0, 2359)),
        "charge_slot_1_end": Def(C.uint16, None, HR(95), valid=(0, 2359)),
        "enable_charge": Def(C.bool, None, HR(96)),
        "battery_low_voltage_protection_limit": Def(C.uint16, C.centi, HR(97)),
        "battery_high_voltage_protection_limit": Def(C.uint16, C.centi, HR(98)),
        # skip voltage adjustment settings 99-104
        ##Adjust Battery Voltage? (From GivTCP list)
        "battery_voltage_adjust": Def(C.uint16, C.centi, HR(105)),
        # skip voltage adjustment settings 106-107
        "battery_low_force_charge_time": Def(C.uint16, None, HR(108)),
        "enable_bms_read": Def(C.bool, None, HR(109)),
        "battery_soc_reserve": Def(C.uint16, None, HR(110)),
        "battery_charge_limit": Def(C.uint16, None, HR(111), valid=(0, 50)),
        "battery_discharge_limit": Def(C.uint16, None, HR(112), valid=(0, 50)),
        "enable_buzzer": Def(C.bool, None, HR(113)),
        "battery_discharge_min_power_reserve": Def(
            C.uint16, None, HR(114), valid=(4, 100)
        ),
        # 'island_check_continue': Def(C.uint16, None, HR(115)),
        "charge_target_soc": Def(C.uint16, None, HR(116), valid=(4, 100)),
        "charge_soc_stop_2": Def(C.uint16, None, HR(117)),
        "discharge_soc_stop_2": Def(C.uint16, None, HR(118)),
        "charge_soc_stop_1": Def(C.uint16, None, HR(119)),
        #
        # Holding Registers, block 120-179
        #
        "discharge_soc_stop_1": Def(C.uint16, None, HR(120)),
        "enable_local_command_test": Def(C.bool, None, HR(121)),
        "power_factor_function_model": Def(C.uint16, PowerFactorFunctionModel, HR(122)),
        "frequency_load_limit_rate": Def(C.uint16, None, HR(123)),
        "enable_low_voltage_fault_ride_through": Def(C.bool, None, HR(124)),
        "enable_frequency_derating": Def(C.bool, None, HR(125)),
        "enable_above_6kw_system": Def(C.bool, None, HR(126)),
        "start_system_auto_test": Def(C.bool, None, HR(127)),
        "enable_spi": Def(C.bool, None, HR(128)),
        # skip PF configuration and protection settings 129-166
        "inverter_reboot": Def(C.uint16, None, HR(163)),
        "threephase_balance_mode": Def(C.uint16, None, HR(167)),
        "threephase_abc": Def(C.uint16, None, HR(168)),
        "threephase_balance_1": Def(C.uint16, None, HR(169)),
        "threephase_balance_2": Def(C.uint16, None, HR(170)),
        "threephase_balance_3": Def(C.uint16, None, HR(171)),
        # HR(172-174) unused
        "enable_battery_on_pv_or_grid": Def(C.bool, None, HR(175)),
        "debug_inverter": Def(C.uint16, None, HR(176)),
        "enable_ups_mode": Def(C.bool, None, HR(177)),
        "enable_g100_limit_switch": Def(C.bool, None, HR(178)),
        "enable_battery_cable_impedance_alarm": Def(C.bool, None, HR(179)),
        #
        # Holding Registers, block 180-239
        #
        "enable_standard_self_consumption_logic": Def(C.bool, None, HR(199)),
        "cmd_bms_flash_update": Def(C.bool, None, HR(200)),

        #
        # Holding Registers 2040-2075
        #
        "plant_status": Def(C.uint16, Status, HR(2040)),
        "expected_inverter_count": Def(C.uint16, None, HR(2041)),
        "expected_meter_count": Def(C.uint16, None, HR(2042)),
        "expected_car_charger_count": Def(C.uint16, None, HR(2043)),
        "discharge_slot_1": Def(C.timeslot, None, HR(2044), HR(2045)),
        "discharge_target_1": Def(C.uint16, None, HR(2046)),
        "discharge_slot_2": Def(C.timeslot, None, HR(2047), HR(2048)),
        "discharge_target_2": Def(C.uint16, None, HR(2049)),
        "discharge_slot_3": Def(C.timeslot, None, HR(2050), HR(2051)),
        "discharge_target_3": Def(C.uint16, None, HR(2052)),
        "charge_slot_1": Def(C.timeslot, None, HR(2053), HR(2054)),
        "charge_target_1": Def(C.uint16, None, HR(2055)),
        "charge_slot_2": Def(C.timeslot, None, HR(2056), HR(2057)),
        "charge_target_2": Def(C.uint16, None, HR(2058)),
        "charge_slot_3": Def(C.timeslot, None, HR(2059), HR(2060)),
        "charge_target_3": Def(C.uint16, None, HR(2061)),
        "export_slot_1": Def(C.timeslot, None, HR(2062), HR(2063)),
        "export_target_1": Def(C.uint16, None, HR(2064)),
        "export_slot_2": Def(C.timeslot, None, HR(2065), HR(2066)),
        "export_target_2": Def(C.uint16, None, HR(2067)),
        "export_slot_3": Def(C.timeslot, None, HR(2068), HR(2069)),
        "export_target_3": Def(C.uint16, None, HR(2070)),
        #"export_power_limit": Def(C.uint16, None, HR(2071)),
        "car_charge_mode": Def(C.uint16, None, HR(2072)),
        "car_charge_boost": Def(C.uint16, None, HR(2073)),
        "plant_charge_compensation": Def(C.uint16, None, HR(2074)),
        "plant_discharge_compensation": Def(C.uint16, None, HR(2075)),
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

