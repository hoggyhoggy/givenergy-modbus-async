"""
High level interpretation of the Three Phase inverter modbus registers.

The 3PH Inverter itself is the primary class; the others are
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

class SystemMode(IntEnum):
    OFFLINE = 0
    GRID_TIED = 1
    
    @classmethod
    def _missing_(cls, value: int):
        """Default to 0."""
        return cls(0)

class BatteryMaintenance(IntEnum):
    OFF = 0
    DISCHARGE = 1
    CHARGE = 2
    STANDBY=3
    
    @classmethod
    def _missing_(cls, value: int):
        """Default to 0."""
        return cls(0)
BatteryMaintenance

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
    
    @classmethod
    def name(cls, value):
        """Return friendly name for use in logs."""
        fname={
            '2':"Hybrid",
            '3':"AC",
            '4':"Hybrid - 3ph",
            '5':"EMS",
            '6':"AC - 3ph",
            '7':"Gateway",
            '8':"All in One",
        }
        return fname.get(value)
    
    @classmethod
    def add_regs(cls, value):
        """Return possible additional registers."""
        regs={
            '2': ([],[180,240,300,360]),    #Hybrid
            '3': ([],[180,240,300,360]),    #AC
            '4': ([1000,1060,1120,1180,1240,1300,1360],[1000,1120]),   #"Hybrid - 3ph"
            '5': ([2040],[2040]),   #EMS
            '6': ([1000,1060,1120,1180,1240,1300,1360],[1000,1120]),   #AC - 3ph
            '7': ([1600],[]),   #Gateway
            '8': ([],[180,240,300,360]),   #All in One
        }
        return regs.get(value)
    

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
    
class BatteryPriority(IntEnum):
    """Battery discharge strategy."""

    LOAD = 0
    BATTERY = 1
    GRID = 2
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

class PVInputMode(IntEnum):
    INDEPENDENT = 0
    ONE_BY_ONE = 1
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

class PowerFactorFunctionModel(IntEnum):
    """Power Factor function model."""

    PF_1 = 0
    PF_BY_SET = 1
    DEFAULT_PF_LINE = 2
    USER_PF_LINE = 3
    UNDER_EXCITED_INDUCTIVE_REACTIVE_POWER = 4
    OVER_EXCITED_CAPACITIVE_REACTIVE_POWER = 5
    QV_MODEL = 6
    DEFAULT_PF_LINE2 = 7
    UNDER_EXCITED_QU_MODE = 8
    OVER_EXCITED_QU_MODE = 8
    @classmethod
    def _missing_(cls, value):
        """Default to 0."""
        return cls(0)

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
    

class ThreePhaseInverter(RegisterGetter, metaclass=DynamicDoc):
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
        "serial_number": Def(C.string, None, HR(13), HR(14), HR(15), HR(16), HR(17)),
        "arm_firmware_version": Def(C.uint16, None, HR(21)),
        "generation": Def(C.uint16, Generation, HR(21)),
        "firmware_version": Def(C.firmware_version, None, HR(19), HR(21)),
        "system_time": Def(C.datetime, None, HR(35), HR(36), HR(37), HR(38), HR(39), HR(40)),
        "enable_inverter_auto_restart": Def((C.duint8, 0), C.bool, HR(53)),
        "enable_inverter": Def((C.duint8, 1), C.bool, HR(53)),
        
        #
        # Three Phase Holding Registers 1000-1124
        #
        "set_command_save": Def(C.bool, None, HR(1001)),
        "active_rate": Def(C.uint16, None, HR(1002)),
        "reactive_rate": Def(C.uint16, None, HR(1003)),
        "set_power_factor": Def(C.uint16, None, HR(1004)),
        "grid_connect_time": Def(C.uint16, None, HR(1007)),
        "grid_reconnect_time": Def(C.uint16, None, HR(1008)),
        "grid_connect_slope": Def(C.deci, None, HR(1009)),
        "com_baud_rate": Def(C.uint16, None, HR(1010)),
        "grid_reconnect_slope": Def(C.uint16, None, HR(1011)),
        "inverter_module": Def(C.uint32, None, (HR(1012),HR(1013))),     #needs type
        "meter_fail_enable": Def(C.uint16, None, HR(1017)),
        "v_grid_low_limit_1": Def(C.deci, None, HR(1018)),
        "v_grid_high_limit_1": Def(C.deci, None, HR(1019)),
        "f_grid_low_limit_1": Def(C.centi, None, HR(1020)),
        "f_grid_high_limit_1": Def(C.centi, None, HR(1021)),
        "v_grid_low_limit_2": Def(C.deci, None, HR(1022)),
        "v_grid_high_limit_2": Def(C.deci, None, HR(1023)),
        "f_grid_low_limit_2": Def(C.centi, None, HR(1024)),
        "f_grid_high_limit_2": Def(C.centi, None, HR(1025)),
        "v_grid_low_limit_3": Def(C.deci, None, HR(1026)),
        "v_grid_high_limit_3": Def(C.deci, None, HR(1027)),
        "f_grid_low_limit_3": Def(C.centi, None, HR(1028)),
        "f_grid_high_limit_3": Def(C.centi, None, HR(1029)),
        "v_grid_low_limit_cee": Def(C.deci, None, HR(1030)),
        "v_grid_high_limit_cee": Def(C.deci, None, HR(1031)),
        "f_grid_low_limit_cee": Def(C.centi, None, HR(1032)),
        "f_grid_high_limit_cee": Def(C.centi, None, HR(1033)),
        "time_grid_low_voltage_limit_1": Def(C.centi, None, HR(1034)),
        "time_grid_high_voltage_limit_1": Def(C.centi, None, HR(1035)),
        "time_grid_low_voltage_limit_2": Def(C.centi, None, HR(1036)),
        "time_grid_high_voltage_limit_2": Def(C.centi, None, HR(1037)),
        "time_grid_low_freq_limit_1": Def(C.centi, None, HR(1038)),
        "time_grid_high_freq_limit_1": Def(C.centi, None, HR(1039)),
        "time_grid_low_freq_limit_2": Def(C.centi, None, HR(1040)),
        "time_grid_high_freq_limit_2": Def(C.centi, None, HR(1041)),
        "v_10min_protect": Def(C.deci, None, HR(1042)),
        "pf_model": Def(C.uint16, PowerFactorFunctionModel, HR(1043)),
        "f_over_derate_start": Def(C.centi, None, HR(1045)),
        "f_over_derate_slope": Def(C.uint16, None, HR(1046)),
        "q_lockin_power": Def(C.uint16, None, HR(1047)),
        "pf_lock_in_voltage": Def(C.deci, None, HR(1049)),
        "pf_lock_out_voltage": Def(C.deci, None, HR(1050)),
        "f_under_derate_slope": Def(C.milli, None, HR(1051)),
        "v_reactive_delay_time": Def(C.milli, None, HR(1052)),
        "time_over_freq_delay_time": Def(C.centi, None, HR(1053)),
        "pf_limit_load_1": Def(C.uint16, None, HR(1054)),
        "pf_limit_pf_1": Def(C.uint16, None, HR(1055)),
        "pf_limit_load_2": Def(C.uint16, None, HR(1056)),
        "pf_limit_pf_2": Def(C.uint16, None, HR(1057)),
        "pf_limit_load_3": Def(C.uint16, None, HR(1058)),
        "pf_limit_pf_3": Def(C.uint16, None, HR(1059)),
        "pf_limit_load_4": Def(C.uint16, None, HR(1060)),
        "pf_limit_pf_4": Def(C.uint16, None, HR(1061)),
        "p_export_limit": Def(C.deci, None, HR(1063)),
        "f_under_derate_start": Def(C.centi, None, HR(1064)),
        "f_under_derate_end": Def(C.centi, None, HR(1065)),
        "f_over_derate_end": Def(C.centi, None, HR(1066)),
        "time_under_freq_derate_delay": Def(C.centi, None, HR(1067)),
        "f_over_derate_stop": Def(C.centi, None, HR(1069)),
        "f_over_derate_recovery_delay": Def(C.centi, None, HR(1070)),
        "zero_current_low_voltage": Def(C.deci, None, HR(1071)),
        "zero_current_high_voltage": Def(C.deci, None, HR(1072)),
        "f_power_on_recovery": Def(C.centi, None, HR(1073)),
        "f_under_derate_stop": Def(C.centi, None, HR(1074)),
        "f_under_derate_recovery_delay": Def(C.centi, None, HR(1075)),
        "pv_input_mode": Def(C.uint16, PVInputMode, HR(1047)),
        "load_first_stop_soc": Def(C.uint16, None, HR(1078)),
        "ac_power_derate_delay": Def(C.centi, None, HR(1079)),
        "battery_type": Def(C.uint16, BatteryType, HR(1080)),
        "max_charge_current": Def(C.uint16, None, HR(1088)),
        "v_battery_LV": Def(C.deci, None, HR(1089)),
        "v_battery_CV": Def(C.deci, None, HR(1090)),
        "lead_acid_number": Def(C.deci, None, HR(1091)),
        "drms_enable": Def(C.uint16, None, HR(1093)),
        "aging_test": Def(C.uint16, None, HR(1098)),
        "bypass_enable": Def(C.uint16, None, HR(1100)),
        "npe_enable": Def(C.uint16, None, HR(1101)),
        "unbalance_output_enable": Def(C.bool, None, HR(1104)),
        "backup_enable": Def(C.bool, None, HR(1105)),
        "v_backup_nominal": Def(C.nominal_voltage, None, HR(1106)),
        "f_backup_nominal": Def(C.nominal_frequency, None, HR(1107)),
        "p_discharge_rate": Def(C.uint16, None, HR(1108)),
        "discharge_stop_soc": Def(C.uint16, None, HR(1109)),
        "p_charge_rate": Def(C.uint16, None, HR(1110)),
        "charge_stop_soc": Def(C.uint16, None, HR(1111)),
        "ac_charge_enable": Def(C.bool, None, HR(1112)),
        "charge_slot_1": Def(C.timeslot, None, HR(1113),HR(1114)),
        "charge_slot_2": Def(C.timeslot, None, HR(1115),HR(1116)),
        "load_compensation_enable": Def(C.bool, None, HR(1117)),
        "discharge_start_time_0": Def(C.timeslot, None, HR(1118),HR(1119)),
        "discharge_start_time_1": Def(C.timeslot, None, HR(1120),HR(1121)),
        "force_discharge_enable": Def(C.uint16, None, HR(1122)),
        "force_charge_enable": Def(C.uint16, None, HR(1123)),
        "battery_maintenance_mode": Def(C.uint16, BatteryMaintenance, HR(1124)),
        
                
        #
        # Input Registers, block 1000-1060 - PV
        #

        "v_pv1": Def(C.deci, None, IR(1001)),
        "v_pv2": Def(C.deci, None, IR(1002)),
        "i_pv1": Def(C.deci, None, IR(1009)),
        "i_pv2": Def(C.deci, None, IR(1010)),
        "p_pv1": Def(C.uint32, None, IR(1017),IR(1018)),
        "p_pv2": Def(C.deci, None, IR(1019),IR(1020)),
        #
        # Input Registers, block 1060-1120 - Grid
        #
        "v_ac1": Def(C.deci, None, IR(1061)),
        "v_ac2": Def(C.deci, None, IR(1062)),
        "v_ac3": Def(C.deci, None, IR(1063)),
        "i_ac1": Def(C.deci, None, IR(1064)),
        "i_ac2": Def(C.deci, None, IR(1065)),
        "i_ac3": Def(C.deci, None, IR(1066)),
        "f_ac1": Def(C.milli, None, IR(1067)),
        "power_factor": Def(C.int16, None, IR(1068)),
        "p_inverter_out": Def(C.uint32, None, IR(1069),IR(1070)),
        "p_inverter_ac_charge": Def(C.uint32, None, IR(1071),IR(1072)),
        "p_grid_apparent": Def(C.uint32, None, IR(1073),IR(1074)),
        "system_mode": Def(C.bool, SystemMode, IR(1075)),
        "status": Def(C.uint16, Status, IR(1076)),
        "start_delay_time": Def(C.uint16, None, IR(1077)),
        "p_meter_import": Def(C.uint32, None, IR(1079),IR(1080)),
        "p_meter_export": Def(C.uint32, None, IR(1081),IR(1082)),
        "p_load_ac1": Def(C.int16, None, IR(1083)),
        "p_load_ac2": Def(C.int16, None, IR(1084)),
        "p_load_ac3": Def(C.int16, None, IR(1085)),
        "p_load_all": Def(C.uint32, None, IR(1089),IR(1090)),
        "p_out_ac1": Def(C.int16, None, IR(1091)),
        "p_out_ac2": Def(C.int16, None, IR(1092)),
        "p_out_ac3": Def(C.int16, None, IR(1093)),
        
        #
        # Input Registers, block 1120-1140 - Battery
        #

        "battery_priority": Def(C.uint16, BatteryPriority, IR(1120)),
        "battery_type": Def(C.int16, BatteryType, IR(1121)),
        "dc_status": Def(C.uint16, Status, IR(1124)),
        "t_inverter": Def(C.deci, None, IR(1128)),
        "t_boost": Def(C.deci, None, IR(1129)),
        "t_buck_boost": Def(C.deci, None, IR(1130)),
        "v_battery_bms": Def(C.deci, None, IR(1131)),
        "battery_soc": Def(C.uint16, None, IR(1132)),
        "v_battery_pcs": Def(C.deci, None, IR(1133)),
        "v_dc_bus": Def(C.deci, None, IR(1134)),
        "v_inv_bus": Def(C.deci, None, IR(1135)),
        "p_battery_discharge": Def(C.uint32, None, IR(1136),IR(1137)),
        "p_battery_charge": Def(C.uint32, None, IR(1138),IR(1139)),
        "i_battery": Def(C.int16, None, IR(1140)),
        
        #
        # Input Registers, block 1180-1240 - EPS
        #
        "f_nominal_eps": Def(C.milli, None, IR(1180)),
        "v_eps_ac1": Def(C.deci, None, IR(1181)),
        "v_eps_ac2": Def(C.deci, None, IR(1182)),
        "v_eps_ac3": Def(C.deci, None, IR(1183)),
        "i_eps_ac1": Def(C.deci, None, IR(1184)),
        "i_eps_ac2": Def(C.deci, None, IR(1185)),
        "i_eps_ac3": Def(C.deci, None, IR(1186)),
        "p_eps_ac1": Def(C.uint32, None, IR(1187),IR(1188)),
        "p_eps_ac2": Def(C.uint32, None, IR(1189),IR(1190)),
        "p_eps_ac3": Def(C.uint32, None, IR(1191),IR(1192)),
        
        #
        # Input Registers, block 1240-1300 - Power
        #
        "p_export": Def(C.uint32, None, IR(1240),IR(1241)),
        "p_meter2": Def(C.uint32, None, IR(1244),IR(1245)),

        #
        # Input Registers, block 1000-1360 - Fault
        #
        
        #
        # Input Registers, block 1360-1413 - Energy
        #
        "e_inverter_out_today": Def(C.uint32, None, IR(1360),IR(1361)),
        "e_inverter_out_total": Def(C.uint32, None, IR(1362),IR(1363)),
        "e_pv1_today": Def(C.uint32, None, IR(1366),IR(1367)),
        "e_pv1_total": Def(C.uint32, None, IR(1368),IR(1369)),
        "e_pv2_today": Def(C.uint32, None, IR(1370),IR(1371)),
        "e_pv2_total": Def(C.uint32, None, IR(1372),IR(1373)),
        "e_pv_total": Def(C.uint32, None, IR(1374),IR(1375)),
        "e_ac_charge_today": Def(C.uint32, None, IR(1376),IR(1377)),
        "e_ac_charge_total": Def(C.uint32, None, IR(1378),IR(1379)),
        "e_import_today": Def(C.uint32, None, IR(1380),IR(1381)),
        "e_import_total": Def(C.uint32, None, IR(1382),IR(1383)),
        "e_export_today": Def(C.uint32, None, IR(1384),IR(1385)),
        "e_export_total": Def(C.uint32, None, IR(1386),IR(1387)),
        "e_battery_discharge_today": Def(C.uint32, None, IR(1388),IR(1389)),
        "e_battery_discharge_total": Def(C.uint32, None, IR(1390),IR(1391)),
        "e_battery_charge_today": Def(C.uint32, None, IR(1392),IR(1393)),
        "e_battery_charge_total": Def(C.uint32, None, IR(1394),IR(1395)),
        "e_load_today": Def(C.uint32, None, IR(1396),IR(1397)),
        "e_load_total": Def(C.uint32, None, IR(1398),IR(1399)),
        "e_export2_today": Def(C.uint32, None, IR(1400),IR(1401)),
        "e_export2_total": Def(C.uint32, None, IR(1402),IR(1403)),
        "e_pv_today": Def(C.uint32, None, IR(1412),IR(1413)),

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
