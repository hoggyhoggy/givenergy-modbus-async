from enum import IntEnum, StrEnum
import math

from pydantic import BaseConfig, create_model

from givenergy_modbus_async.model.register import HR, IR
from givenergy_modbus_async.model.register import (
    Converter as C,
)
from givenergy_modbus_async.model.register import (
    RegisterDefinition as Def,
)
from givenergy_modbus_async.model.register import (
    RegisterGetter,
)

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
    
class State(IntEnum):
    """Inverter status."""

    STATIC = 0
    CHARGE = 1
    DISCHARGE = 2
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

class MeterType(IntEnum):
    """Installed meter type."""

    CT_OR_EM418 = 0
    EM115 = 1
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


class UsbDevice(IntEnum):
    """USB devices that can be inserted into inverters."""

    NONE = 0
    WIFI = 1
    DISK = 2
    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)

class InverterRegisterGetter(RegisterGetter):
    """Structured format for all inverter attributes."""

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
        "first_battery_serial_number": Def(C.string, None, HR(8), HR(9), HR(10), HR(11), HR(12)),
        "serial_number": Def(C.string, None, HR(13), HR(14), HR(15), HR(16), HR(17)),
        "first_battery_bms_firmware_version": Def(C.uint16, None, HR(18)),
        "dsp_firmware_version": Def(C.uint16, None, HR(19)),
        "enable_charge_target": Def(C.bool, None, HR(20)),
        "arm_firmware_version": Def(C.uint16, None, HR(21)),
        "generation": Def(C.uint16, Generation, HR(21)),
        "firmware_version": Def(C.firmware_version, None, HR(19), HR(21)),
        "usb_device_inserted": Def(C.uint16, UsbDevice, HR(22)),
        "select_arm_chip": Def(C.bool, None, HR(23)),
        "variable_address": Def(C.uint16, None, HR(24)),
        "variable_value": Def(C.uint16, None, HR(25)),
        "grid_port_max_power_output": Def(C.uint16, None, HR(26)),
        "battery_power_mode": Def(C.uint16, BatteryPowerMode, HR(27)),
        "enable_60hz_freq_mode": Def(C.bool, None, HR(28)),
        "soc_force_adjust": Def(C.uint16, BatteryCalibrationStage, HR(29)),
        "modbus_address": Def(C.uint16, None, HR(30)),
        "charge_slot_2": Def(C.timeslot, None, HR(31), HR(32)),
        "user_code": Def(C.uint16, None, HR(33)),
        "modbus_version": Def(C.centi, (C.fstr, "0.2f"), HR(34)),
        "system_time": Def(C.datetime, None, HR(35), HR(36), HR(37), HR(38), HR(39), HR(40)),
        "enable_drm_rj45_port": Def(C.bool, None, HR(41)),
        "enable_reversed_ct_clamp": Def(C.bool, None, HR(42)),
        "charge_soc": Def((C.duint8, 0), None, HR(43)),
        "discharge_soc": Def((C.duint8, 1), None, HR(43)),
        "discharge_slot_2": Def(C.timeslot, None, HR(44), HR(45)),
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
        "enable_charge": Def(C.bool, None, HR(96)),
        "battery_low_voltage_protection_limit": Def(C.uint16, C.centi, HR(97)),
        "battery_high_voltage_protection_limit": Def(C.uint16, C.centi, HR(98)),
        # skip voltage adjustment settings 99-105
        "battery_voltage_adjust": Def(C.uint16, C.centi, HR(105)), ##Adjust Battery Voltage? (From GivTCP list)
        # skip voltage adjustment settings 106-107
        "battery_low_force_charge_time": Def(C.uint16, None, HR(108)),
        "enable_bms_read": Def(C.bool, None, HR(109)),
        "battery_soc_reserve": Def(C.uint16, None, HR(110)),
        "battery_charge_limit": Def(C.uint16, None, HR(111)),
        "battery_discharge_limit": Def(C.uint16, None, HR(112)),
        "enable_buzzer": Def(C.bool, None, HR(113)),
        "battery_discharge_min_power_reserve": Def(C.uint16, None, HR(114)),
        # 'island_check_continue': Def(C.uint16, None, HR(115)),
        "charge_target_soc": Def(C.uint16, None, HR(116)),  # requires enable_charge_target
        "charge_soc_stop_2": Def(C.uint16, None, HR(117)),
        "discharge_soc_stop_2": Def(C.uint16, None, HR(118)),
        "charge_soc_stop_1": Def(C.uint16, None, HR(119)),
        #
        # Holding Registers, block 180-239
        #
        "enable_standard_self_consumption_logic": Def(C.bool, None, HR(199)),
        "cmd_bms_flash_update": Def(C.bool, None, HR(200)),
        # 202-239 - Gen 2+ only
        "charge_target_soc_1": Def(C.uint16, None, HR(242)),
        "charge_slot_2": Def(C.timeslot, None, HR(243), HR(244)),
        "charge_target_soc_2": Def(C.uint16, None, HR(245)),
        "charge_slot_3": Def(C.timeslot, None, HR(246), HR(247)),
        "charge_target_soc_3": Def(C.uint16, None, HR(248)),
        "charge_slot_4": Def(C.timeslot, None, HR(249), HR(250)),
        "charge_target_soc_4": Def(C.uint16, None, HR(251)),
        "charge_slot_5": Def(C.timeslot, None, HR(252), HR(253)),
        "charge_target_soc_5": Def(C.uint16, None, HR(254)),
        "charge_slot_6": Def(C.timeslot, None, HR(255), HR(256)),
        "charge_target_soc_6": Def(C.uint16, None, HR(257)),
        "charge_slot_7": Def(C.timeslot, None, HR(258), HR(259)),
        "charge_target_soc_7": Def(C.uint16, None, HR(260)),
        "charge_slot_8": Def(C.timeslot, None, HR(261), HR(262)),
        "charge_target_soc_8": Def(C.uint16, None, HR(263)),
        "charge_slot_9": Def(C.timeslot, None, HR(264), HR(265)),
        "charge_target_soc_9": Def(C.uint16, None, HR(266)),
        "charge_slot_10": Def(C.timeslot, None, HR(267), HR(268)),
        "charge_target_soc_10": Def(C.uint16, None, HR(269)),
        "discharge_target_soc_1": Def(C.uint16, None, HR(272)),
        "discharge_target_soc_2": Def(C.uint16, None, HR(275)),
        "discharge_slot_3": Def(C.timeslot, None, HR(276), HR(277)),
        "discharge_target_soc_3": Def(C.uint16, None, HR(278)),
        "discharge_slot_4": Def(C.timeslot, None, HR(279), HR(280)),
        "discharge_target_soc_4": Def(C.uint16, None, HR(281)),
        "discharge_slot_5": Def(C.timeslot, None, HR(282), HR(283)),
        "discharge_target_soc_5": Def(C.uint16, None, HR(284)),
        "discharge_slot_6": Def(C.timeslot, None, HR(285), HR(286)),
        "discharge_target_soc_6": Def(C.uint16, None, HR(287)),
        "discharge_slot_7": Def(C.timeslot, None, HR(288), HR(289)),
        "discharge_target_soc_7": Def(C.uint16, None, HR(290)),
        "discharge_slot_8": Def(C.timeslot, None, HR(291), HR(292)),
        "discharge_target_soc_8": Def(C.uint16, None, HR(293)),
        "discharge_slot_9": Def(C.timeslot, None, HR(294), HR(295)),
        "discharge_target_soc_9": Def(C.uint16, None, HR(296)),
        "discharge_slot_10": Def(C.timeslot, None, HR(297), HR(298)),
        "discharge_target_soc_10": Def(C.uint16, None, HR(299)),
        #
        # Holding Registers, block 300-479
        # Single Phase New registers
        #
        "battery_charge_limit_ac": Def(C.uint16, None, HR(313)),
        "battery_discharge_limit_ac": Def(C.uint16, None, HR(314)),
        "battery_pause_mode": Def(C.uint16, BatteryPauseMode, HR(318)),
        "battery_pause_slot_1": Def(C.timeslot, None, HR(319), HR(320)),

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
        "fault_warning": Def(C.uint32, None, IR(1622),IR(1623)),
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


class InverterConfig(BaseConfig):
    """Pydantic configuration for the Inverter class."""

    orm_mode = True
    getter_dict = InverterRegisterGetter


Gateway = create_model(
    "Gateway", __config__=InverterConfig, **InverterRegisterGetter.to_fields()
)  # type: ignore[call-overload]
