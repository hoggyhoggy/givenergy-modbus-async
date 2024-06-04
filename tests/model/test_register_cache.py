import datetime

from givenergy_modbus.model import TimeSlot
from givenergy_modbus.model.register import HR, IR
from givenergy_modbus.model.register_cache import RegisterCache
from tests.model.test_register import HOLDING_REGISTERS, INPUT_REGISTERS


def test_register_cache(register_cache):
    """Ensure we can instantiate a RegisterCache and set registers in it."""
    expected = {HR(k): v for k, v in HOLDING_REGISTERS.items()}
    expected.update({IR(k): v for k, v in INPUT_REGISTERS.items()})
    assert register_cache == expected


def test_to_from_json():
    """Ensure we can unserialize a RegisterCache from JSON."""
    assert RegisterCache.from_json('{"HR(1)": 2, "IR(3)": 4}') == {HR(1): 2, IR(3): 4}


def test_to_from_json_actual_data(json_inverter_daytime_discharging_with_solar_generation):
    """Ensure we can unserialize a RegisterCache to and from JSON."""
    rc = RegisterCache.from_json(json_inverter_daytime_discharging_with_solar_generation)
    assert len(rc) == 360
