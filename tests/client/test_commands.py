from datetime import datetime
import pytest

from givenergy_modbus.client.client import Client
from givenergy_modbus.model import TimeSlot
from givenergy_modbus.model.inverter import BatteryPauseMode
from givenergy_modbus.pdu import WriteHoldingRegisterRequest


class RegisterMap:
    """Mapping of holding register function to location."""

    ENABLE_CHARGE_TARGET = 20
    BATTERY_POWER_MODE = 27
    SOC_FORCE_ADJUST = 29
    CHARGE_SLOT_2_START = 243
    CHARGE_SLOT_2_END = 244
    SYSTEM_TIME_YEAR = 35
    SYSTEM_TIME_MONTH = 36
    SYSTEM_TIME_DAY = 37
    SYSTEM_TIME_HOUR = 38
    SYSTEM_TIME_MINUTE = 39
    SYSTEM_TIME_SECOND = 40
    DISCHARGE_SLOT_2_START = 44
    DISCHARGE_SLOT_2_END = 45
    ACTIVE_POWER_RATE = 50
    DISCHARGE_SLOT_1_START = 56
    DISCHARGE_SLOT_1_END = 57
    ENABLE_DISCHARGE = 59
    CHARGE_SLOT_1_START = 94
    CHARGE_SLOT_1_END = 95
    ENABLE_CHARGE = 96
    BATTERY_SOC_RESERVE = 110
    BATTERY_CHARGE_LIMIT = 111
    BATTERY_DISCHARGE_LIMIT = 112
    BATTERY_DISCHARGE_MIN_POWER_RESERVE = 114
    CHARGE_TARGET_SOC = 116
    REBOOT = 163
    BATTERY_PAUSE_MODE = 318



client = Client('foo', 1234)
commands = client.commands

async def test_configure_charge_target():
    """Ensure we can set and disable a charge target."""
    assert commands.set_charge_target(45) == [
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE, True),
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE_TARGET, True),
        WriteHoldingRegisterRequest(RegisterMap.CHARGE_TARGET_SOC, 45),
    ]
    assert commands.set_charge_target(100) == [
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE, True),
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE_TARGET, False),
        WriteHoldingRegisterRequest(RegisterMap.CHARGE_TARGET_SOC, 100),
    ]

    with pytest.raises(ValueError, match=r'0 out of range for charge_target_soc'):
        commands.set_charge_target(0)
    with pytest.raises(ValueError, match=r'1 out of range for charge_target_soc'):
        commands.set_charge_target(1)
    with pytest.raises(ValueError, match=r'101 out of range for charge_target_soc'):
        commands.set_charge_target(101)

    assert commands.disable_charge_target() == [
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE_TARGET, False),
        WriteHoldingRegisterRequest(RegisterMap.CHARGE_TARGET_SOC, 100),
    ]


async def test_set_charge():
    """Ensure we can toggle charging."""
    assert commands.set_enable_charge(True) == [WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE, True)]
    assert commands.set_enable_charge(False) == [WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE, False)]
    with pytest.warns(DeprecationWarning):
        assert commands.enable_charge() == [WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE, True)]
    with pytest.warns(DeprecationWarning):
        assert commands.disable_charge() == [WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE, False)]


async def test_set_discharge():
    """Ensure we can toggle discharging."""
    assert commands.set_enable_discharge(True) == [WriteHoldingRegisterRequest(RegisterMap.ENABLE_DISCHARGE, True)]
    assert commands.set_enable_discharge(False) == [WriteHoldingRegisterRequest(RegisterMap.ENABLE_DISCHARGE, False)]
    with pytest.warns(DeprecationWarning):
        assert commands.enable_discharge() == [WriteHoldingRegisterRequest(RegisterMap.ENABLE_DISCHARGE, True)]
    with pytest.warns(DeprecationWarning):
        assert commands.disable_discharge() == [WriteHoldingRegisterRequest(RegisterMap.ENABLE_DISCHARGE, False)]


async def test_set_battery_discharge_mode():
    """Ensure we can set a discharge mode."""
    assert commands.set_discharge_mode_max_power() == [WriteHoldingRegisterRequest(RegisterMap.BATTERY_POWER_MODE, 0)]
    assert commands.set_discharge_mode_to_match_demand() == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_POWER_MODE, 1)
    ]

def test_set_battery_pause_mode():
    """Test battery_pause_mode"""
    assert commands.set_battery_pause_mode(BatteryPauseMode.DISABLED) == [WriteHoldingRegisterRequest(RegisterMap.BATTERY_PAUSE_MODE, 0)]
    assert commands.set_battery_pause_mode(BatteryPauseMode.PAUSE_CHARGE) == [WriteHoldingRegisterRequest(RegisterMap.BATTERY_PAUSE_MODE, 1)]
    assert commands.set_battery_pause_mode(BatteryPauseMode.PAUSE_DISCHARGE) == [WriteHoldingRegisterRequest(RegisterMap.BATTERY_PAUSE_MODE, 2)]
    assert commands.set_battery_pause_mode(BatteryPauseMode.PAUSE_BOTH) == [WriteHoldingRegisterRequest(RegisterMap.BATTERY_PAUSE_MODE, 3)]
    with pytest.raises(ValueError, match=r'5 out of range for battery_pause_mode'):
        commands.set_battery_pause_mode(5)
                                                                            
@pytest.mark.parametrize('action', ('charge', 'discharge'))
@pytest.mark.parametrize('slot', (1, 2))
@pytest.mark.parametrize('hour1', (0, 23))
@pytest.mark.parametrize('min1', (0, 59))
@pytest.mark.parametrize('hour2', (0, 23))
@pytest.mark.parametrize('min2', (0, 59))
async def test_set_charge_slots(action: str, slot: int, hour1: int, min1: int, hour2: int, min2: int):
    """Ensure we can set charge time slots correctly."""
    # test set and reset functions for the relevant {action} and {slot}
    messages = getattr(commands, f'set_{action}_slot_{slot}')(TimeSlot.from_components(hour1, min1, hour2, min2))

    hr_start = getattr(RegisterMap, f'{"CHARGE" if action == "charge" else "DISCHARGE"}_SLOT_{slot}_START')
    hr_end = getattr(RegisterMap, f'{"CHARGE" if action == "charge" else "DISCHARGE"}_SLOT_{slot}_END')
    assert messages == [
        WriteHoldingRegisterRequest(hr_start, 100 * hour1 + min1),
        WriteHoldingRegisterRequest(hr_end, 100 * hour2 + min2),
    ]

    assert getattr(commands, f'reset_{action}_slot_{slot}')() == [
        WriteHoldingRegisterRequest(hr_start, 0),
        WriteHoldingRegisterRequest(hr_end, 0),
    ]


async def test_set_mode_dynamic():
    """Ensure we can set the inverter to dynamic mode."""
    assert commands.set_mode_dynamic() == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_POWER_MODE, 1),
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_SOC_RESERVE, 4),
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_DISCHARGE, False),
    ]


async def test_set_mode_storage():
    """Ensure we can set the inverter to a storage mode with discharge slots."""
    assert commands.set_mode_storage(TimeSlot.from_components(1, 2, 3, 4)) == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_POWER_MODE, 1),
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_SOC_RESERVE, 100),
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_DISCHARGE, True),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_1_START, 102),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_1_END, 304),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_2_START, 0),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_2_END, 0),
    ]

    assert commands.set_mode_storage(TimeSlot.from_components(5, 6, 7, 8), TimeSlot.from_components(9, 10, 11, 12)) == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_POWER_MODE, 1),
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_SOC_RESERVE, 100),
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_DISCHARGE, True),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_1_START, 506),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_1_END, 708),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_2_START, 910),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_2_END, 1112),
    ]

    assert commands.set_mode_storage(TimeSlot.from_repr(1314, 1516), discharge_for_export=True) == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_POWER_MODE, 0),
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_SOC_RESERVE, 100),
        WriteHoldingRegisterRequest(RegisterMap.ENABLE_DISCHARGE, True),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_1_START, 1314),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_1_END, 1516),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_2_START, 0),
        WriteHoldingRegisterRequest(RegisterMap.DISCHARGE_SLOT_2_END, 0),
    ]


async def test_set_charge_and_discharge_limits():
    """Ensure we can set a charge limit."""
    assert commands.set_battery_charge_limit(1) == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_CHARGE_LIMIT, 1),
    ]

    assert commands.set_battery_discharge_limit(1) == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_DISCHARGE_LIMIT, 1),
    ]

    assert commands.set_battery_charge_limit(50) == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_CHARGE_LIMIT, 50),
    ]

    assert commands.set_battery_discharge_limit(50) == [
        WriteHoldingRegisterRequest(RegisterMap.BATTERY_DISCHARGE_LIMIT, 50),
    ]

    with pytest.raises(ValueError, match=r'51 out of range for battery_charge_limit'):
        commands.set_battery_charge_limit(51)
    with pytest.raises(ValueError, match=r'51 out of range for battery_discharge_limit'):
        commands.set_battery_discharge_limit(51)


async def test_set_system_time():
    """Ensure set_system_time emits the correct requests."""
    assert commands.set_system_date_time(datetime(year=2022, month=11, day=23, hour=4, minute=34, second=59)) == [
        WriteHoldingRegisterRequest(RegisterMap.SYSTEM_TIME_YEAR, 22),
        WriteHoldingRegisterRequest(RegisterMap.SYSTEM_TIME_MONTH, 11),
        WriteHoldingRegisterRequest(RegisterMap.SYSTEM_TIME_DAY, 23),
        WriteHoldingRegisterRequest(RegisterMap.SYSTEM_TIME_HOUR, 4),
        WriteHoldingRegisterRequest(RegisterMap.SYSTEM_TIME_MINUTE, 34),
        WriteHoldingRegisterRequest(RegisterMap.SYSTEM_TIME_SECOND, 59),
    ]


async def test_set_inverter_reboot():
    """Ensure set_inverter_reboot emits the correct requests."""
    assert commands.set_inverter_reboot() == [
        WriteHoldingRegisterRequest(RegisterMap.REBOOT, 100),
    ]
