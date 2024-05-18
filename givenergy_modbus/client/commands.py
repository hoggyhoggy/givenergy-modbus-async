"""High-level methods for interacting with a remote system.

NOTE: it is no longer intended that applications import this
directly. Instead, they should access commands via client.commands

These don't actually send requests to the inverter.
They simply prepare sequences of requests that need to be sent using
the client.
"""

from datetime import datetime
from typing import Optional
from typing_extensions import deprecated  # type: ignore[attr-defined]

from .client import Client
from ..model import TimeSlot
from ..model.inverter import (
    Inverter,
    BatteryPauseMode,
)
from ..pdu import (
    ReadHoldingRegistersRequest,
    ReadInputRegistersRequest,
    TransparentRequest,
    WriteHoldingRegisterRequest,
)


class Commands:
    """High-level methods for interacting with a remote system."""

    def __init__(self, client: Client):
        self.client = client

    # Helper to look up an inverter holding register by name
    # and prepare a write request. Value range checking gets
    # done automatically.
    def write_named_register(self, name: str, value: int) -> TransparentRequest:
        """Prepare a request to write to a register."""
        idx = Inverter.lookup_writable_register(name, value)
        return WriteHoldingRegisterRequest(idx, value)

    def refresh_plant_data(
        self, complete: bool, number_batteries: int = 1, max_batteries: int = 5
    ) -> list[TransparentRequest]:
        """Refresh plant data."""
        requests: list[TransparentRequest] = [
            ReadInputRegistersRequest(
                base_register=0, register_count=60, slave_address=0x32
            ),
            ReadInputRegistersRequest(
                base_register=180, register_count=60, slave_address=0x32
            ),
        ]
        if complete:
            requests.append(
                ReadHoldingRegistersRequest(
                    base_register=0, register_count=60, slave_address=0x32
                )
            )
            requests.append(
                ReadHoldingRegistersRequest(
                    base_register=60, register_count=60, slave_address=0x32
                )
            )
            requests.append(
                ReadHoldingRegistersRequest(
                    base_register=120, register_count=60, slave_address=0x32
                )
            )
            requests.append(
                ReadInputRegistersRequest(
                    base_register=120, register_count=60, slave_address=0x32
                )
            )
            number_batteries = max_batteries
        for i in range(number_batteries):
            requests.append(
                ReadInputRegistersRequest(
                    base_register=60, register_count=60, slave_address=0x32 + i
                )
            )
        return requests

    def disable_charge_target(self) -> list[TransparentRequest]:
        """Removes SOC limit and target 100% charging."""
        return [
            self.write_named_register('enable_charge_target', False),
            self.write_named_register('charge_target_soc', 100),
        ]

    def set_charge_target(self, target_soc: int) -> list[TransparentRequest]:
        """Sets inverter to stop charging when SOC reaches the desired level. Also referred to as "winter mode"."""
        ret = self.set_enable_charge(True)
        if target_soc == 100:
            ret.extend(self.disable_charge_target())
        else:
            ret.append(
                self.write_named_register('enable_charge_target', True),
            )
            ret.append(
                self.write_named_register('charge_target_soc', target_soc),
            )
        return ret

    def set_enable_charge(self, enabled: bool) -> list[TransparentRequest]:
        """Enable the battery to charge, depending on the mode and slots set."""
        return [self.write_named_register('enable_charge', enabled)]

    def set_enable_discharge(self, enabled: bool) -> list[TransparentRequest]:
        """Enable the battery to discharge, depending on the mode and slots set."""
        return [self.write_named_register('enable_discharge', enabled)]

    def set_inverter_reboot(self) -> list[TransparentRequest]:
        """Restart the inverter."""
        return [self.write_named_register('inverter_reboot', 100)]

    def set_calibrate_battery_soc(self) -> list[TransparentRequest]:
        """Set the inverter to recalibrate the battery state of charge estimation."""
        return [self.write_named_register('soc_force_adjust', 1)]

    @deprecated("use set_enable_charge(True) instead")
    def enable_charge(self) -> list[TransparentRequest]:
        """Enable the battery to charge, depending on the mode and slots set."""
        return self.set_enable_charge(True)

    @deprecated("use set_enable_charge(False) instead")
    def disable_charge(self) -> list[TransparentRequest]:
        """Prevent the battery from charging at all."""
        return self.set_enable_charge(False)

    @deprecated("use set_enable_discharge(True) instead")
    def enable_discharge(self) -> list[TransparentRequest]:
        """Enable the battery to discharge, depending on the mode and slots set."""
        return self.set_enable_discharge(True)

    @deprecated("use set_enable_discharge(False) instead")
    def disable_discharge(self) -> list[TransparentRequest]:
        """Prevent the battery from discharging at all."""
        return self.set_enable_discharge(False)

    def set_discharge_mode_max_power(self) -> list[TransparentRequest]:
        """Set the battery discharge mode to maximum power, exporting to the grid if it exceeds load demand."""
        return [self.write_named_register('battery_power_mode', 0)]

    def set_discharge_mode_to_match_demand(self) -> list[TransparentRequest]:
        """Set the battery discharge mode to match demand, avoiding exporting power to the grid."""
        return [self.write_named_register('battery_power_mode', 1)]

    @deprecated("Use set_battery_soc_reserve(val) instead")
    def set_shallow_charge(self, val: int) -> list[TransparentRequest]:
        """Set the minimum level of charge to maintain."""
        return self.set_battery_soc_reserve(val)

    def set_battery_soc_reserve(self, val: int) -> list[TransparentRequest]:
        """Set the minimum level of charge to maintain."""
        # TODO what are valid values? 4-100?
        return [self.write_named_register('battery_soc_reserve', val)]

    def set_battery_charge_limit(self, val: int) -> list[TransparentRequest]:
        """Set the battery charge power limit as percentage. 50% (2.6 kW) is the maximum for most inverters."""
        return [self.write_named_register('battery_charge_limit', val)]

    def set_battery_discharge_limit(self, val: int) -> list[TransparentRequest]:
        """Set the battery discharge power limit as percentage. 50% (2.6 kW) is the maximum for most inverters."""
        return [self.write_named_register('battery_discharge_limit', val)]

    def set_battery_power_reserve(self, val: int) -> list[TransparentRequest]:
        """Set the battery power reserve to maintain."""
        return [self.write_named_register('battery_discharge_min_power_reserve', val)]

    def set_battery_pause_mode(self, val: BatteryPauseMode) -> list[TransparentRequest]:
        """Set the battery pause mode."""
        return [self.write_named_register('battery_pause_mode', val)]

    def _set_charge_slot(
        self, discharge: bool, idx: int, slot: Optional[TimeSlot]
    ) -> list[TransparentRequest]:
        chdis = 'discharge' if discharge else 'charge'
        if slot:
            start = slot.start.hour * 100 + slot.start.minute
            end = slot.end.hour * 100 + slot.end.minute
        else:
            start = 0
            end = 0
        return [
            self.write_named_register(f"{chdis}_slot_{idx}_start", start),
            self.write_named_register(f"{chdis}_slot_{idx}_end", end),
        ]

    def set_charge_slot_1(self, timeslot: TimeSlot) -> list[TransparentRequest]:
        """Set first charge slot start & end times."""
        return self._set_charge_slot(False, 1, timeslot)

    def reset_charge_slot_1(self) -> list[TransparentRequest]:
        """Reset first charge slot to zero/disabled."""
        return self._set_charge_slot(False, 1, None)

    def set_charge_slot_2(self, timeslot: TimeSlot) -> list[TransparentRequest]:
        """Set second charge slot start & end times."""
        return self._set_charge_slot(False, 2, timeslot)

    def reset_charge_slot_2(self) -> list[TransparentRequest]:
        """Reset second charge slot to zero/disabled."""
        return self._set_charge_slot(False, 2, None)

    def set_discharge_slot_1(self, timeslot: TimeSlot) -> list[TransparentRequest]:
        """Set first discharge slot start & end times."""
        return self._set_charge_slot(True, 1, timeslot)

    def reset_discharge_slot_1(self) -> list[TransparentRequest]:
        """Reset first discharge slot to zero/disabled."""
        return self._set_charge_slot(True, 1, None)

    def set_discharge_slot_2(self, timeslot: TimeSlot) -> list[TransparentRequest]:
        """Set second discharge slot start & end times."""
        return self._set_charge_slot(True, 2, timeslot)

    def reset_discharge_slot_2(self) -> list[TransparentRequest]:
        """Reset second discharge slot to zero/disabled."""
        return self._set_charge_slot(True, 2, None)

    # TODO: this needs a bit more finesse
    # client.exec() does everything in parallel, and therefore in random
    # order. Will take several elapsed seconds to send all the components.
    # If either new or target seconds is close to 60, then the minutes
    # may not end up set correctly.
    # Should probably accept dt of None to means "now", and then it can
    # do things in a suitable order to ensure that the target time is
    # properly synchronised (eg send seconds first, unless it's close
    # to 60, in which case maybe send year/month/day, then wait for seconds
    # to wrap, then send hour/min/sec

    def set_system_date_time(self, dt: datetime) -> list[TransparentRequest]:
        """Set the date & time of the inverter."""
        return [
            self.write_named_register("system_time_year", dt.year - 2000),
            self.write_named_register("system_time_month", dt.month),
            self.write_named_register("system_time_day", dt.day),
            self.write_named_register("system_time_hour", dt.hour),
            self.write_named_register("system_time_minute", dt.minute),
            self.write_named_register("system_time_second", dt.second),
        ]

    def set_mode_dynamic(self) -> list[TransparentRequest]:
        """Set system to Dynamic / Eco mode.

        This mode is designed to maximise use of solar generation. The battery will
        charge from excess solar generation to avoid exporting power, and discharge
        to meet load demand when solar power is insufficient to avoid importing power.
        This mode is useful if you want to maximise self-consumption of renewable
        generation and minimise the amount of energy drawn from the grid.
        """
        # r27=1 r110=4 r59=0
        return (
            self.set_discharge_mode_to_match_demand()
            + self.set_battery_soc_reserve(4)
            + self.set_enable_discharge(False)
        )

    def set_mode_storage(
        self,
        discharge_slot_1: TimeSlot = TimeSlot.from_repr(1600, 700),
        discharge_slot_2: Optional[TimeSlot] = None,
        discharge_for_export: bool = False,
    ) -> list[TransparentRequest]:
        """Set system to storage mode with specific discharge slots(s).

        This mode stores excess solar generation during the day and holds that energy
        ready for use later in the day. By default, the battery will start to discharge
        from 4pm-7am to cover energy demand during typical peak hours. This mode is
        particularly useful if you get charged more for your electricity at certain
        times to utilise the battery when it is most effective. If the second time slot
        isn't specified, it will be cleared.

        You can optionally also choose to export excess energy: instead of discharging
        to meet only your load demand, the battery will discharge at full power and any
        excess will be exported to the grid. This is useful if you have a variable
        export tariff (e.g. Agile export) and you want to target the peak times of
        day (e.g. 4pm-7pm) when it is most valuable to export energy.
        """
        if discharge_for_export:
            ret = self.set_discharge_mode_max_power()  # r27=0
        else:
            ret = self.set_discharge_mode_to_match_demand()  # r27=1
        ret.extend(self.set_battery_soc_reserve(100))  # r110=100
        ret.extend(self.set_enable_discharge(True))  # r59=1
        ret.extend(self.set_discharge_slot_1(discharge_slot_1))  # r56=1600, r57=700
        if discharge_slot_2:
            ret.extend(self.set_discharge_slot_2(discharge_slot_2))  # r56=1600, r57=700
        else:
            ret.extend(self.reset_discharge_slot_2())
        return ret
