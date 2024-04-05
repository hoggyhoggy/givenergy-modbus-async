#!/usr/bin/env python3

import asyncio
import json
from functools import wraps
from urllib.request import urlopen

##begin added
from givenergy_modbus.client.commands import *
##end added

from givenergy_modbus.client.client import Client
#from givenergy_modbus.client import Timeslot, commands
from givenergy_modbus.client import commands

import typer
from givenergy_modbus.pdu import ReadHoldingRegistersRequest
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

console = Console()

console.print("""Givenergy Modbus(async)""" )

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
    """Polls Inverter in a loop and displays key inverter values in CLI as they come in."""
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
        #table.add_row('[b]Model', f'{inverter.inverter_model.name}, type code 0x{inverter.device_type_code}, module 0x{inverter.inverter_module:04x}')
        table.add_row('[b]Serial number', plant.inverter_serial_number)
        table.add_row('[b]Data adapter serial number', plant.data_adapter_serial_number)
        #table.add_row('[b]Firmware version', inverter.inverter_firmware_version)
        table.add_row('[b]System time', inverter.system_time.isoformat(sep=" "))
        #table.add_row('[b]Status', f'{inverter.inverter_status} (fault code: {inverter.fault_code})')
        table.add_row('[b]System mode', str(inverter.system_mode))
        table.add_row('[b]USB device inserted', str(inverter.usb_device_inserted))
        table.add_row('[b]Total work time', f'{inverter.work_time_total}h')
        table.add_row('[b]Inverter heatsink', f'{inverter.temp_inverter_heatsink}°C')
        table.add_row('[b]Charger', f'{inverter.temp_charger}°C')
        table.add_row('[b]Battery temp', f'{inverter.temp_battery}°C')
        table.add_row('[b]Number of batteries', str(len(batteries)))
        ##added to live update table:
        table.add_row('[b]Inverter SOC', str(inverter.battery_percent))
        table.add_row('[b]Battery Volt', str(inverter.v_battery))
        table.add_row('[b]Battery Power', str(inverter.p_battery))
        table.add_row('[b]Demand', str(inverter.p_load_demand))
        table.add_row('[b]Grid In/Out', str(inverter.p_grid_out))
        table.add_row('[b]Inverter Power', str(inverter.p_inverter_out))
        table.add_row('[b]Grid In/Out', str(inverter.p_pv1))
        table.add_row('[b]Inverter Power', str(inverter.p_pv2))
        return table

    with Live(auto_refresh=False) as live:
        while True:
            live.update(generate_table(), refresh=True)
            await asyncio.sleep(1)

################# Battery Power Commands ######################
            
@main.async_command()
async def set_charge_power(val, host: str = '0.0.0.0', port: int = 8899):
    """[0-50] Set the battery charge power limit (scaled 0-50) Note: steps are basically total cap (kWh) x10."""
    client = Client(host=host, port=port)
    command = set_battery_charge_limit(val)[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

@main.async_command()
async def set_discharge_power(val, host: str = '0.0.0.0', port: int = 8899):
    """[0-50] Set the battery discharge power limit (scaled 0-50) Note: steps are basically total cap (kWh) x10."""
    client = Client(host=host, port=port)
    command = set_battery_discharge_limit(val)[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

################### Battery Settings ########################

@main.async_command()
async def set_charge_target(val, host: str = '0.0.0.0', port: int = 8899):
    """[4-100]% - Sets inverter to stop charging on AC ONLY when SOC reaches the desired level."""
    client = Client(host=host, port=port)
    command = set_charge_target_only(val)[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

@main.async_command()
async def set_reserve_target(val, host: str = '0.0.0.0', port: int = 8899):
    """[4-100]% - Set the minimum level of charge to maintain."""
    client = Client(host=host, port=port)
    command = set_battery_soc_reserve(val)[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

@main.async_command()
async def bat_discharge(val: bool, host: str = '0.0.0.0', port: int = 8899):
    """[TRUE / FALSE] - Enable the battery to discharge, depending on the mode and slots set."""
    client = Client(host=host, port=port)
    command = set_enable_discharge(val)[0]
    responder(command,host,port,val)

################### Inverter Settings #####################

@main.async_command()
async def set_ac_charge(val: bool, host: str = '0.0.0.0', port: int = 8899):
    """[TRUE / FALSE] - Enable the battery to charge on AC, depending on the mode and slots set."""
    client = Client(host=host, port=port)
    command = set_enable_charge(val)[0]
    responder(command,host,port,val)

@main.async_command()
async def eco_on(val: str = 'ECO ENABLED', host: str = '0.0.0.0', port: int = 8899):
    """Set the battery discharge mode to match demand, avoiding importing power from the grid."""
    client = Client(host=host, port=port)
    command = set_discharge_mode_to_match_demand()[0]
    responder(command,host,port,val)

@main.async_command()
async def eco_off(val: str = 'ECO DISABLED', host: str = '0.0.0.0', port: int = 8899):
    """Disables ECO mode which may export at full power to the grid if export slots are set"""
    client = Client(host=host, port=port)
    command = set_discharge_mode_max_power()[0]
    responder(command,host,port,val)


################### Time Slots ######################


#ToDo


######  Examples  #######

###### Basic Call Example ######
#@main.async_command()
async def dummy_call(val: str = 'enabled', host: str = '0.0.0.0', port: int = 8899):
    """Dummy call that just repeats back commands sent to & received from commands.py for testing"""
    client = Client(host=host, port=port)
    command = set_discharge_mode_to_match_demand()[0]
    responder(command,host,port,val)

###### Pass Bool Example ######
#@main.async_command()
async def dummy_call2(val: bool, host: str = '0.0.0.0', port: int = 8899):
    """Dummy call that just repeats back commands sent to & received from commands.py for testing"""
    client = Client(host=host, port=port)
    command = set_enable_charge(val)[0]
    responder(command,host,port,val)

###### Pass Value Example ######
#@main.async_command()
async def dummy_call3(val, host: str = '0.0.0.0', port: int = 8899):
    """Dummy call that just repeats back commands sent to & received from commands.py for testing"""
    client = Client(host=host, port=port)
    command = set_battery_discharge_limit(val)[0]
    responder(command,host,port,val)

    
@main.command()
def aa():
    """Example usage: 'givenergy-modbus set-charge-power 50 --host 192.168.1.151' """
    console.print("""##Example usage: 'givenergy-modbus set-charge-power 50 --host 192.168.1.151' """)


#Function Generates CLI table with commands passed/sent - Does not check received/actioned by inverter!
def responder(command,host,port,val):
    table = Table(title='Status', show_header=False, box=None)
    table.add_row('[b]Command:', str(command))
    table.add_row('[b]Sent to:', str(host))
    table.add_row('[b]Port:', str(port))
    table.add_row('[b]Value Sent:', str(val))
    console.print(table)
    
#if __name__ == "__main__":
 #   app()
