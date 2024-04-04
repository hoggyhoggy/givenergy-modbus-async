#!/usr/bin/env python3

import asyncio
import json
from functools import wraps
from urllib.request import urlopen

##begin added LH
from typing import Optional
from arrow import Arrow
from typing_extensions import deprecated  # type: ignore[attr-defined]
from givenergy_modbus.client.commands import RegisterMap

from givenergy_modbus.pdu import (
    ReadHoldingRegistersRequest,
    ReadInputRegistersRequest,
    TransparentRequest,
    WriteHoldingRegisterRequest,
)
##end LH added


from givenergy_modbus.client.client import Client
#from givenergy_modbus.client import Timeslot, commands
from givenergy_modbus.client import commands

import typer
#from givenergy_modbus.pdu import ReadHoldingRegistersRequest
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

console = Console()


class AsyncTyper(typer.Typer):
    def async_command(self, *args, **kwargs):
        def decorator(async_func):
            @wraps(async_func)
            def sync_func(*_args, **_kwargs):
                return asyncio.run(async_func(*_args, **_kwargs))

            self.command(*args, **kwargs)(sync_func)
            return async_func

        return decorator


main = AsyncTyper()


@main.async_command()
async def watch_plant(host: str = '0.0.0.0', port: int = 8899):
#async def watch_plant(host: str = '192.168.1.151', port: int = 8899):
    client = Client(host=host, port=port)
    await client.connect()
    await client.execute([
        ReadHoldingRegistersRequest(base_register=0, register_count=60, slave_address=0x32),
        ReadHoldingRegistersRequest(base_register=60, register_count=60, slave_address=0x32),
        ReadHoldingRegistersRequest(base_register=120, register_count=60, slave_address=0x32),
    ],
        retries=3, timeout=1.0)

    def generate_table() -> Table:
        plant = client.plant
        try:
            inverter = plant.inverter
        except KeyError as e:
            return f'awaiting data...'
        batteries = plant.batteries

        table = Table(title='[b]Inverter', show_header=False, box=None)
        table.add_row('[b]Model', f'{inverter.inverter_model.name}, type code 0x{inverter.device_type_code}, module 0x{inverter.inverter_module:04x}')
        table.add_row('[b]Serial number', plant.inverter_serial_number)
        table.add_row('[b]Data adapter serial number', plant.data_adapter_serial_number)
        table.add_row('[b]Firmware version', inverter.inverter_firmware_version)
        table.add_row('[b]System time', inverter.system_time.isoformat(sep=" "))
        table.add_row('[b]Status', f'{inverter.inverter_status} (fault code: {inverter.fault_code})')
        table.add_row('[b]System mode', str(inverter.system_mode))
        table.add_row('[b]Charge status', str(inverter.charge_status))
        table.add_row('[b]USB device inserted', str(inverter.usb_device_inserted))
        table.add_row('[b]Total work time', f'{inverter.work_time_total}h')
        table.add_row('[b]Inverter heatsink', f'{inverter.temp_inverter_heatsink}°C')
        table.add_row('[b]Charger', f'{inverter.temp_charger}°C')
        table.add_row('[b]Battery temp', f'{inverter.temp_battery}°C')
        table.add_row('[b]Number of batteries', str(len(batteries)))
        return table

    with Live(auto_refresh=False) as live:
        while True:
            live.update(generate_table(), refresh=True)
            await asyncio.sleep(1)


@main.command()
def my_normal_command():
    table = Table(title='[b]Inverter', show_header=False, box=None)
    table.add_row('[b]Model', 'Hybrid')
    table.add_row('[b]type code', '2001')
    table.add_row('[b]Serial number', 'SA2114G047')
    table.add_row('[b]Data adapter serial number', 'WF2125G316')
    table.add_row('[b]Firmware version', 'D0.449-A0.449')
    table.add_section()
    console.print(table)

@main.command()
#def charge_target(host: str = '0.0.0.0', port: int = 8899) -> list[TransparentRequest]:
def charge_target(host: str = '0.0.0.0', port: int = 8899) -> list[TransparentRequest]:
    """Removes SOC limit and target 100% charging."""
    return [
        #WriteHoldingRegisterRequest(RegisterMap.ENABLE_CHARGE_TARGET, False),
        WriteHoldingRegisterRequest(RegisterMap.CHARGE_TARGET_SOC, 50),
    ]

#if __name__ == "__main__":
 #   app()
