from enum import IntEnum

from pydantic import BaseConfig, create_model

from givenergy_modbus_async.model.register import IR
from givenergy_modbus_async.model.register import (
    Converter as DT,
)
from givenergy_modbus_async.model.register import (
    RegisterDefinition as Def,
)
from givenergy_modbus_async.model.register import (
    RegisterGetter,
)

"""
Addr:0x70~0x8F
Register start address = (Register base NO) + 240  * (BAMS_Addr  -  0x90);
"""


class UsbDevice(IntEnum):
    """USB devices that can be inserted into batteries."""

    NONE = 0
    DISK = 8
    UNKNOWN = 257


class BatteryRegisterGetter(RegisterGetter):
    """Structured format for all battery attributes."""

    REGISTER_LUT = {
        # Input Registers, block 60-119
        "pack_software_version": Def(
            DT.string, None, IR(60), IR(61), IR(62), IR(63)),
        "number_of_module": Def(DT.uint16, None, IR(64)),
        "cells_per_module": Def(DT.uint16, None, IR(65)),
        "cluster_cell_voltage": Def(DT.uint16, None, IR(67)),
        "cluster_cell_temperature": Def(DT.uint16, None, IR(68)),
        "status": Def(DT.uint16, None, IR(70)),
        "battery_voltage": Def(DT.deci, None, IR(73)),
        "load_voltage": Def(DT.deci, None, IR(74)),
        "battery_current": Def(DT.milli, None, IR(76)),
        "battery_power": Def(DT.milli, None, IR(79)),
        "battery_soc": Def(DT.uint16, None, IR(80)),
        "battery_soh": Def(DT.uint16, None, IR(81)),
        "charge_energy_total": Def(DT.uint32, None, IR(82),IR(83)),
        "discharge_energy_total": Def(DT.uint32, None, IR(84),IR(85)),
        "charge_capacity_total": Def(DT.uint32, None, IR(86),IR(87)),
        "discharge_capacity_total": Def(DT.uint32, None, IR(88),IR(89)),
        "charge_energy_today": Def(DT.uint32, None, IR(90),IR(91)),
        "discharge_energy_today": Def(DT.uint32, None, IR(92),IR(93)),
        "charge_capacity_today": Def(DT.uint32, None, IR(94),IR(95)),
        "discharge_capacity_today": Def(DT.uint32, None, IR(96),IR(97)),
        "design_battery_capacity": Def(DT.deci, None, IR(98)),
        "remaining_battery_capacity": Def(DT.deci, None, IR(99)),
        "number_of_cycles": Def(DT.deci, None, IR(100)),
        "min_discharge_voltage": Def(DT.deci, None, IR(102)),
        "min_charge_voltage": Def(DT.deci, None, IR(103)),
        "min_discharge_current": Def(DT.deci, None, IR(104)),
        "min_charge_current": Def(DT.deci, None, IR(105)),
    }


class BatteryConfig(BaseConfig):
    """Pydantic configuration for the Battery class."""

    orm_mode = True
    getter_dict = BatteryRegisterGetter


_Battery = create_model(
    "Battery", __config__=BatteryConfig, **BatteryRegisterGetter.to_fields()
)  # type: ignore[call-overload]


class Battery(_Battery):  # type: ignore[misc,valid-type]
    """Add some utility methods to the base pydantic class."""

    def is_valid(self) -> bool:
        """Try to detect if a battery exists based on its attributes."""
        return self.serial_number not in (
            None,
            "",
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            "          ",
        )

