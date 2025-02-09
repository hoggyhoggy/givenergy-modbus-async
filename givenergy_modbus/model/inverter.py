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


class UsbDevice(IntEnum):
    """USB devices that can be inserted into inverters."""

    NONE = 0
    WIFI = 1
    DISK = 2


class BatteryPowerMode(IntEnum):
    """Battery discharge strategy."""

    EXPORT = 0
    SELF_CONSUMPTION = 1


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


class MeterType(IntEnum):
    """Installed meter type."""

    CT_OR_EM418 = 0
    EM115 = 1


class BatteryType(IntEnum):
    """Installed battery type."""

    LEAD_ACID = 0
    LITHIUM = 1


class BatteryPauseMode(IntEnum):
    """Battery pause mode."""

    DISABLED = 0
    PAUSE_CHARGE = 1
    PAUSE_DISCHARGE = 2
    PAUSE_BOTH = 3


class PowerFactorFunctionModel(IntEnum):
    """Power Factor function model."""

    PF_1 = 0
    PF_BY_SET = 1
    DEFAULT_PF_LINE = 2
    USER_PF_LINE = 3
    UNDER_EXCITED_INDUCTIVE_REACTIVE_POWER = 4
    OVER_EXCITED_CAPACITIVE_REACTIVE_POWER = 5
    QV_MODEL = 6


class Status(IntEnum):
    """Inverter status."""

    WAITING = 0
    NORMAL = 1
    WARNING = 2
    FAULT = 3
    FLASHING_FIRMWARE_UPDATE = 4


class Phase(StrEnum):
    """Determine number of Phases."""

    OnePhase = ("Single Phase",)
    ThreePhase = ("Three Phase",)

    __dtc_to_phases_lut__ = {
        2: OnePhase,
        3: OnePhase,
        4: ThreePhase,
        5: OnePhase,
        6: ThreePhase,
        7: OnePhase,
        8: OnePhase,
    }

    @classmethod
    def from_device_type_code(cls, device_type_code: str):
        """Return the appropriate model from a given serial number."""
        prefix = int(device_type_code[0])
        if prefix in cls.__dtc_to_phases_lut__:
            return cls.__dtc_to_phases_lut__[prefix]
        else:
            # raise UnknownModelError(f"Cannot determine model number from serial number {serial_number}")
            return 'Unknown'


class InvertorPower(StrEnum):
    """Map Invertor max power"""

    __dtc_to_power_lut__ = {
        '2001': 5000,
        '2002': 4600,
        '2003': 3600,
        '3001': 3000,
        '3002': 3600,
        '4001': 6000,
        '4002': 8000,
        '4003': 10000,
        '4004': 11000,
        '8001': 6000,
    }

    @classmethod
    def from_dtc_power(cls, dtc: str):
        """Return the appropriate model from a given serial number."""
        if dtc in cls.__dtc_to_power_lut__:
            return cls.__dtc_to_power_lut__[dtc]
        else:
            return 0


class Inverter(RegisterGetter, metaclass=DynamicDoc):
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
        "soc_force_adjust": Def(
            C.uint16, BatteryCalibrationStage, HR(29), valid=(0, 3)
        ),
        "modbus_address": Def(C.uint16, None, HR(30)),
        # gen-1 defines HR(31)/HR(32) as charge_slot_2, but later generations
        # define it at HR(243)/HR(244) instead.
        # It doesn't seem to work on gen-1 anyway (changes get overwritten),
        # so just leave HR(31) and HR(32) undefined for now.
        "user_code": Def(C.uint16, None, HR(33)),
        "modbus_version": Def(C.centi, (C.fstr, "0.2f"), HR(34)),
        "system_time": Def(
            C.datetime, None, HR(35), HR(36), HR(37), HR(38), HR(39), HR(40)
        ),
        "system_time_year": Def(C.uint16, None, HR(35), valid=(0, 65535)),
        "system_time_month": Def(C.uint16, None, HR(36), valid=(1, 12)),
        "system_time_day": Def(C.uint16, None, HR(37), valid=(1, 31)),
        "system_time_hour": Def(C.uint16, None, HR(38), valid=(0, 23)),
        "system_time_minute": Def(C.uint16, None, HR(39), valid=(0, 59)),
        "system_time_second": Def(C.uint16, None, HR(40), valid=(0, 59)),
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
        "enable_discharge": Def(C.bool, None, HR(59), valid=(0, 1)),
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
        "enable_charge": Def(C.bool, None, HR(96), valid=(0, 1)),
        "battery_low_voltage_protection_limit": Def(C.uint16, C.centi, HR(97)),
        "battery_high_voltage_protection_limit": Def(C.uint16, C.centi, HR(98)),
        # skip voltage adjustment settings 99-104
        ##Adjust Battery Voltage? (From GivTCP list)
        "battery_voltage_adjust": Def(C.uint16, C.centi, HR(105)),
        # skip voltage adjustment settings 106-107
        "battery_low_force_charge_time": Def(C.uint16, None, HR(108)),
        "enable_bms_read": Def(C.bool, None, HR(109)),
        "battery_soc_reserve": Def(C.uint16, None, HR(110), valid=(4, 100)),
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
        "inverter_reboot": Def(C.uint16, None, HR(163), valid=(100, 100)),
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
        # 202-239 - Gen 2 only
        "charge_target_soc_1": Def(C.uint16, None, HR(242), valid=(4, 100)),
        "charge_slot_2": Def(C.timeslot, None, HR(243), HR(244)),
        "charge_slot_2_start": Def(C.uint16, None, HR(243), valid=(0, 2359)),
        "charge_slot_2_end": Def(C.uint16, None, HR(244), valid=(0, 2359)),
        "charge_target_soc_2": Def(C.uint16, None, HR(245), valid=(4, 100)),
        "charge_slot_3": Def(C.timeslot, None, HR(246), HR(247)),
        "charge_slot_3_start": Def(C.uint16, None, HR(246), valid=(0, 2359)),
        "charge_slot_3_end": Def(C.uint16, None, HR(247), valid=(0, 2359)),
        "charge_target_soc_3": Def(C.uint16, None, HR(248), valid=(4, 100)),
        "charge_slot_4": Def(C.timeslot, None, HR(249), HR(250)),
        "charge_slot_4_start": Def(C.uint16, None, HR(249), valid=(0, 2359)),
        "charge_slot_4_end": Def(C.uint16, None, HR(250), valid=(0, 2359)),
        "charge_target_soc_4": Def(C.uint16, None, HR(251), valid=(4, 100)),
        "charge_slot_5": Def(C.timeslot, None, HR(252), HR(253)),
        "charge_slot_5_start": Def(C.uint16, None, HR(252), valid=(0, 2359)),
        "charge_slot_5_end": Def(C.uint16, None, HR(253), valid=(0, 2359)),
        "charge_target_soc_5": Def(C.uint16, None, HR(254), valid=(4, 100)),
        "charge_slot_6": Def(C.timeslot, None, HR(255), HR(256)),
        "charge_slot_6_start": Def(C.uint16, None, HR(255), valid=(0, 2359)),
        "charge_slot_6_end": Def(C.uint16, None, HR(256), valid=(0, 2359)),
        "charge_target_soc_6": Def(C.uint16, None, HR(257), valid=(4, 100)),
        "charge_slot_7": Def(C.timeslot, None, HR(258), HR(259)),
        "charge_slot_7_start": Def(C.uint16, None, HR(258), valid=(0, 2359)),
        "charge_slot_7_end": Def(C.uint16, None, HR(259), valid=(0, 2359)),
        "charge_target_soc_7": Def(C.uint16, None, HR(260), valid=(4, 100)),
        "charge_slot_8": Def(C.timeslot, None, HR(261), HR(262)),
        "charge_slot_8_start": Def(C.uint16, None, HR(261), valid=(0, 2359)),
        "charge_slot_8_end": Def(C.uint16, None, HR(262), valid=(0, 2359)),
        "charge_target_soc_8": Def(C.uint16, None, HR(263), valid=(4, 100)),
        "charge_slot_9": Def(C.timeslot, None, HR(264), HR(265)),
        "charge_slot_9_start": Def(C.uint16, None, HR(264), valid=(0, 2359)),
        "charge_slot_9_end": Def(C.uint16, None, HR(265), valid=(0, 2359)),
        "charge_target_soc_9": Def(C.uint16, None, HR(266), valid=(4, 100)),
        "charge_slot_10": Def(C.timeslot, None, HR(267), HR(268)),
        "charge_slot_10_start": Def(C.uint16, None, HR(267), valid=(0, 2359)),
        "charge_slot_10_end": Def(C.uint16, None, HR(268), valid=(0, 2359)),
        "charge_target_soc_10": Def(C.uint16, None, HR(269), valid=(4, 100)),
        "discharge_target_soc_1": Def(C.uint16, None, HR(272)),
        "discharge_target_soc_2": Def(C.uint16, None, HR(275)),
        "discharge_slot_3": Def(C.timeslot, None, HR(276), HR(277)),
        "discharge_slot_3_start": Def(C.uint16, None, HR(276), valid=(0, 2359)),
        "discharge_slot_3_end": Def(C.uint16, None, HR(277), valid=(0, 2359)),
        "discharge_target_soc_3": Def(C.uint16, None, HR(278)),
        "discharge_slot_4": Def(C.timeslot, None, HR(279), HR(280)),
        "discharge_slot_4_start": Def(C.uint16, None, HR(279), valid=(0, 2359)),
        "discharge_slot_4_end": Def(C.uint16, None, HR(280), valid=(0, 2359)),
        "discharge_target_soc_4": Def(C.uint16, None, HR(281)),
        "discharge_slot_5": Def(C.timeslot, None, HR(282), HR(283)),
        "discharge_slot_5_start": Def(C.uint16, None, HR(282), valid=(0, 2359)),
        "discharge_slot_5_end": Def(C.uint16, None, HR(283), valid=(0, 2359)),
        "discharge_target_soc_5": Def(C.uint16, None, HR(284)),
        "discharge_slot_6": Def(C.timeslot, None, HR(285), HR(286)),
        "discharge_slot_6_start": Def(C.uint16, None, HR(285), valid=(0, 2359)),
        "discharge_slot_6_end": Def(C.uint16, None, HR(286), valid=(0, 2359)),
        "discharge_target_soc_6": Def(C.uint16, None, HR(287)),
        "discharge_slot_7": Def(C.timeslot, None, HR(288), HR(289)),
        "discharge_slot_7_start": Def(C.uint16, None, HR(288), valid=(0, 2359)),
        "discharge_slot_7_end": Def(C.uint16, None, HR(289), valid=(0, 2359)),
        "discharge_target_soc_7": Def(C.uint16, None, HR(290)),
        "discharge_slot_8": Def(C.timeslot, None, HR(291), HR(292)),
        "discharge_slot_8_start": Def(C.uint16, None, HR(291), valid=(0, 2359)),
        "discharge_slot_8_end": Def(C.uint16, None, HR(292), valid=(0, 2359)),
        "discharge_target_soc_8": Def(C.uint16, None, HR(293)),
        "discharge_slot_9": Def(C.timeslot, None, HR(294), HR(295)),
        "discharge_slot_9_start": Def(C.uint16, None, HR(294), valid=(0, 2359)),
        "discharge_slot_9_end": Def(C.uint16, None, HR(295), valid=(0, 2359)),
        "discharge_target_soc_9": Def(C.uint16, None, HR(296)),
        "discharge_slot_10": Def(C.timeslot, None, HR(297), HR(298)),
        "discharge_slot_10_start": Def(C.uint16, None, HR(297), valid=(0, 2359)),
        "discharge_slot_10_end": Def(C.uint16, None, HR(298), valid=(0, 2359)),
        "discharge_target_soc_10": Def(C.uint16, None, HR(299)),
        #
        # Holding Registers, block 300-479
        # Single Phase New registers
        #
        "battery_charge_limit_ac": Def(C.uint16, None, HR(313)),
        "battery_discharge_limit_ac": Def(C.uint16, None, HR(314)),
        "battery_pause_mode": Def(C.uint16, BatteryPauseMode, HR(318), valid=(0, 3)),
        "battery_pause_slot_1": Def(C.timeslot, None, HR(319), HR(320)),
        "battery_pause_slot_1_start": Def(C.uint16, None, HR(319), valid=(0, 2359)),
        "battery_pause_slot_1_end": Def(C.uint16, None, HR(320), valid=(0, 2359)),
        #
        # Holding Registers, block 480-539
        # EMS AC3 only
        #
        #
        # Holding Registers, block 1000-1124
        # Three phase Hybrid
        #
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
        #
        # Input Registers, block 0-59
        #
        "status": Def(C.uint16, Status, IR(0)),
        "v_pv1": Def(C.deci, None, IR(1)),
        "v_pv2": Def(C.deci, None, IR(2)),
        "v_p_bus": Def(C.deci, None, IR(3)),
        "v_n_bus": Def(C.deci, None, IR(4)),
        "v_ac1": Def(C.deci, None, IR(5)),
        "e_battery_throughput_total": Def(C.uint32, C.deci, IR(6), IR(7)),
        "i_pv1": Def(C.deci, None, IR(8)),
        "i_pv2": Def(C.deci, None, IR(9)),
        "i_ac1": Def(C.deci, None, IR(10)),
        "e_pv_total": Def(C.uint32, C.deci, IR(11), IR(12)),
        "f_ac1": Def(C.centi, None, IR(13)),
        "v_highbrigh_bus": Def(C.deci, None, IR(15)),  ##HV Bus??? (from Givtcp?)
        "e_pv1_day": Def(C.deci, None, IR(17)),
        "p_pv1": Def(C.uint16, None, IR(18)),
        "e_pv2_day": Def(C.deci, None, IR(19)),
        "p_pv2": Def(C.uint16, None, IR(20)),
        "e_grid_out_total": Def(C.uint32, C.deci, IR(21), IR(22)),
        "e_solar_diverter": Def(C.deci, None, IR(23)),
        "p_inverter_out": Def(C.int16, None, IR(24)),
        "e_grid_out_day": Def(C.deci, None, IR(25)),
        "e_grid_in_day": Def(C.deci, None, IR(26)),
        "e_inverter_in_total": Def(C.uint32, C.deci, IR(27), IR(28)),
        "e_discharge_year": Def(C.deci, None, IR(29)),
        "p_grid_out": Def(C.int16, None, IR(30)),
        "p_eps_backup": Def(C.uint16, None, IR(31)),
        "e_grid_in_total": Def(C.uint32, C.deci, IR(32), IR(33)),
        "e_inverter_in_day": Def(C.deci, None, IR(35)),
        "e_battery_charge_today": Def(C.deci, None, IR(36)),
        "e_battery_discharge_today": Def(C.deci, None, IR(37)),
        "inverter_countdown": Def(C.uint16, None, IR(38)),
        # FAULT_CODE_H = (39, {'type': T_BITFIELD})
        # FAULT_CODE_L = (40, {'type': T_BITFIELD})
        "temp_inverter_heatsink": Def(C.deci, None, IR(41)),
        "p_load_demand": Def(C.uint16, None, IR(42)),
        "p_grid_apparent": Def(C.uint16, None, IR(43)),
        "e_inverter_out_day": Def(C.deci, None, IR(44)),
        "e_inverter_out_total": Def(C.uint32, C.deci, IR(45), IR(46)),
        "work_time_total": Def(C.uint32, None, IR(47), IR(48)),
        "system_mode": Def(C.uint16, None, IR(49)),
        "v_battery": Def(C.centi, None, IR(50)),
        "i_battery": Def(C.centi, None, IR(51)),
        "p_battery": Def(C.int16, None, IR(52)),
        "v_eps_backup": Def(C.deci, None, IR(53)),
        "f_eps_backup": Def(C.centi, None, IR(54)),
        "temp_charger": Def(C.deci, None, IR(55)),
        "temp_battery": Def(C.deci, None, IR(56)),
        "i_grid_port": Def(C.centi, None, IR(58)),
        "battery_percent": Def(C.uint16, None, IR(59)),
        "e_battery_discharge_total": Def(C.deci, None, IR(105)),
        "e_battery_charge_total": Def(C.deci, None, IR(106)),
        "e_battery_discharge_total2": Def(C.deci, None, HR(180)),
        "e_battery_charge_total2": Def(C.deci, None, IR(181)),
        "e_battery_discharge_today2": Def(C.deci, None, IR(182)),
        "e_battery_charge_today2": Def(C.deci, None, IR(183)),
        #
        # Input Registers, block 1000-1119
        # Three phase Hybrid
        #
        #
        # Input Registers, block 1600-1631
        # Gateway
        #
    }

    # @computed('p_pv')
    # def compute_p_pv(p_pv1: int, p_pv2: int, **kwargs) -> int:
    #     """Computes the discharge slot 2."""
    #     return p_pv1 + p_pv2

    # @computed('e_pv_day')
    # def compute_e_pv_day(e_pv1_day: float, e_pv2_day: float, **kwargs) -> float:
    #     """Computes the discharge slot 2."""
    #     return e_pv1_day + e_pv2_day

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
