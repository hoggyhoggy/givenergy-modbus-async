#!/usr/bin/env python3

import asyncio
import json
from functools import wraps
from urllib.request import urlopen

##begin added
from givenergy_modbus_async.client.commands import *
from datetime import datetime
##end added

from givenergy_modbus_async.client.client import Client
#from givenergy_modbus_async.client import Timeslot, commands
from givenergy_modbus_async.client import commands

import typer
from givenergy_modbus_async.pdu import ReadHoldingRegistersRequest
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
async def detect(host: str = '0.0.0.0', port: int = 8899):
    """Dummy call that just repeats back commands sent to & received from commands.py for testing"""  
    client = Client(host=host, port=port)
    await client.connect()
    await client.detect_plant()
    await client.close()
    print (str(client.plant.number_batteries))
    print (str(client.plant.additional_holding_registers))
    print (str(client.plant.slave_address))


@main.async_command()
async def watch_plant2(host: str = '0.0.0.0', port: int = 8899):
    """Polls Inverter in a loop and displays key inverter values in CLI as they come in."""
    client = Client(host=host, port=port)
    await client.connect()
    await client.detect_plant()
    await client.refresh_plant(True, number_batteries=client.plant.number_batteries, retries=3, timeout=3.0)
    
    def generate_table() -> Table:
        plant = client.plant
        try:
            inverter = plant.inverter
        except KeyError as e:
            return f'awaiting data...'
        ##sort this out for multiple bats
        batteries = plant.batteries #test for bat registers

        table = Table(title='[b]Watch Plant Mode', show_header=False, box=None)
        #table.add_row('[b]Model', f'{inverter.inverter_model.name}, type code 0x{inverter.device_type_code}, module 0x{inverter.inverter_module:04x}')
        table.add_row('[b]---Inverter Details---')
        table.add_row('[b]Inv Serial:',plant.inverter_serial_number,'[b]Dongle Serial:',plant.data_adapter_serial_number)       
        table.add_row('[b]Inverter Model:',f'{inverter.model}','[b]Inv. Gen:',f'{inverter.generation}','[b]Inv. Rating',f'{inverter.inverter_max_power}W')
        table.add_row('[b]Max Export Setting:', f'{inverter.grid_port_max_power_output}W','[b]PV Start V:', f'{inverter.v_pv_start}V')
        table.add_row('[b]Internal DC Busses -','[b]V_p_bus:',f'{inverter.v_p_bus}V','[b]V_n_bus:',f'{inverter.v_n_bus}V','[b]HV Bus?:',f'{inverter.v_highbrigh_bus}V')
        table.add_row('[b]External DC Busses -','[b]Bat Terminals:', f'{str(inverter.v_battery)}V')
        table.add_row('[b]Total work time', f'{inverter.work_time_total}h')
        table.add_row()
        table.add_row('[b]---Inverter State---')
        table.add_row('[b]System mode:', str(inverter.system_mode),'[b]Auto Bat Type:', str(inverter.enable_auto_judge_battery_type)) 
        table.add_row('[b]UPS Fast Switch:', str(inverter.enable_ups_mode),'[b]Is Lithium?:', str(inverter.battery_type)) 
        table.add_row('[b]Eco Mode:', str(inverter.battery_power_mode),'[b]BMS Auto Set:', str(inverter.enable_bms_read))
        table.add_row('[b]DC Discharge', str(inverter.enable_discharge),'[b]Total Bat Cap:', f'{str(inverter.battery_capacity)}AH')
        table.add_row('[b]AC Charge Target:', f'{str(inverter.enable_charge_target)}','[b]Bat Calib.:', f'Step: {str(inverter.battery_calibration_stage)} / 7')
        table.add_row()
        table.add_row('[b]---System Targets---')
        table.add_row('[b]Target SOC:', f'{str(inverter.charge_target_soc)}%')
        table.add_row('[b]Reserve SOC:', f'{str(inverter.battery_soc_reserve)}%')
        table.add_row('[b]Minimum SOC:', f'{str(inverter.battery_discharge_min_power_reserve)}%')       
        table.add_row('[b]Charge Power:',f'{str(inverter.battery_charge_limit)} / 50','[b]Disch. Power:',f'{str(inverter.battery_discharge_limit)} / 50')
        table.add_row()
        table.add_row('[b]---System Temps---')
        table.add_row('[b]Inv. Heatsink','[b]Inv. Charger','[b]Battery temp')
        table.add_row(f'{inverter.temp_inverter_heatsink}°C',f'{inverter.temp_charger}°C',f'{inverter.temp_battery}°C')
        table.add_row()
        table.add_row('[b]---System Power---')
        table.add_row('[b]Demand','[b]Grid In/Out','[b]Inverter Power','[b]EPS Power')
        table.add_row(f'{str(inverter.p_load_demand)}W', f'{str(inverter.p_grid_out)}W', f'{str(inverter.p_inverter_out)}W',f'{str(inverter.p_eps_backup)}W')
        table.add_row()
        table.add_row('[b]---Grid Data---')
        table.add_row('[b]Voltage','[b]Current','[b]Frequency')
        table.add_row(f'{str(inverter.v_ac1)}V', f'{str(inverter.i_ac1)}A', f'{str(inverter.f_ac1)}Hz')
        table.add_row()
        table.add_row('[b]---PV Data---')
        table.add_row('[b]PV String 1','[b]PV String 2')
        table.add_row(f'{str(inverter.p_pv1)}W', f'{str(inverter.p_pv2)}W')
        table.add_row(f'{str(inverter.i_pv1)}A', f'{str(inverter.i_pv2)}A')
        table.add_row(f'{str(inverter.v_pv1)}V', f'{str(inverter.v_pv2)}V')
        #table.add_row('[b]Firmware version', inverter.inverter_firmware_version)
        #table.add_row('[b]System time', inverter.system_time.isoformat(sep=" "))
        #table.add_row('[b]Status', f'{inverter.inverter_status} (fault code: {inverter.fault_code})')
        table.add_row()
        table.add_row('[b]---Battery Data---')
        table.add_row('[b]Number of batteries', str(len(batteries)))
        #######sort multiple battery addressing out################
        for i in range(len(batteries)):
            table.add_row('[b]Battery No. ', f'{str(i)}',' - ',f'{str(batteries[i].serial_number)}')
            table.add_row('[b]Inverter Combined SOC', f'{str(inverter.battery_percent)}%')
            table.add_row('[b]Battery ', f'{i}', ' Raw SOC', f'{str(batteries[i].soc)}%','[b]Bat Cycles:', f'{str(batteries[i].num_cycles)}')
            table.add_row('[b]Battery ', f'{i}', ' Volt', f'{str(batteries[i].v_out)}V','[b]Design Cap:', f'{str(batteries[i].cap_design)}AH')
            table.add_row('[b]Battery ', f'{i}', ' Current', f'{str(inverter.i_battery)}A','[b]Calib Cap:', f'{str(batteries[i].cap_calibrated)}AH')
            table.add_row('[b]Battery ', f'{i}', ' Power', f'{str(inverter.p_battery)}W','[b]Remaining Cap:', f'{str(batteries[i].cap_remaining)}AH')
            table.add_row('[b]UV Limit:', f'{str(inverter.battery_low_voltage_protection_limit)}V','[b]OV Limit:', f'{str(inverter.battery_high_voltage_protection_limit)}V','[b]Bat #Volt Adjust?:', f'{str(inverter.battery_voltage_adjust)}V')
            table.add_row()
            table.add_row('[b]---Bat ', f'{i}', ' Cell Data---')
            table.add_row('[b]Cell 1', f'{str(batteries[i].v_cell_01)}V','[b]Cell 2', f'{str(batteries[i].v_cell_02)}V','[b]Cell 3', f'{str(batteries[i].v_cell_03)}V','[b]Cell 4', f'{str(batteries[i].v_cell_04)}V')
            table.add_row('[b]Cell 5', f'{str(batteries[i].v_cell_05)}V','[b]Cell 6', f'{str(batteries[i].v_cell_06)}V','[b]Cell 7', f'{str(batteries[i].v_cell_07)}V','[b]Cell 8', f'{str(batteries[i].v_cell_08)}V')
            table.add_row('[b]Cell 9', f'{str(batteries[i].v_cell_09)}V','[b]Cell 10', f'{str(batteries[i].v_cell_10)}V','[b]Cell 11', f'{str(batteries[i].v_cell_11)}V','[b]Cell 12', f'{str(batteries[i].v_cell_12)}V')
            table.add_row('[b]Cell 13', f'{str(batteries[i].v_cell_13)}V','[b]Cell 14', f'{str(batteries[i].v_cell_14)}V','[b]Cell 15', f'{str(batteries[i].v_cell_15)}V','[b]Cell 16', f'{str(batteries[i].v_cell_16)}V')
        
        return table

    with Live(auto_refresh=False) as live:
        while True:
            live.update(generate_table(), refresh=True)
            await client.refresh_plant(True, number_batteries=1, retries=3, timeout=1.0)
            await asyncio.sleep(10)

@main.async_command()
async def test(host: str = '0.0.0.0', port: int = 8899):
    """Polls Inverter in a loop and displays key inverter values in CLI as they come in."""
    client = Client(host=host, port=port)
    print (client.plant.number_batteries)
    await client.connect()
    await client.detect_plant()
    print (client.plant.number_batteries)
    await client.refresh_plant(True, number_batteries=client.plant.number_batteries, retries=3, timeout=1.0)
    #await client.watch_plant(host, port)
    await client.close()
    print (client.plant.inverter)

@main.async_command()
async def watch_plant(host: str = '0.0.0.0', port: int = 8899):
    """Polls Inverter in a loop and displays key inverter values in CLI as they come in."""
    client = Client(host=host, port=port)
    await client.connect()
    await client.execute([
        ReadHoldingRegistersRequest(base_register=0, register_count=60, slave_address=0x32),
        ReadHoldingRegistersRequest(base_register=60, register_count=60, slave_address=0x32),
        ReadHoldingRegistersRequest(base_register=120, register_count=60, slave_address=0x32),
    ],
        retries=3, timeout=3.0)

    def generate_table() -> Table:
        plant = client.plant
        try:
            inverter = plant.inverter
        except KeyError as e:
            return f'awaiting data...'
        ##sort this out for multiple bats
        batteries = plant.batteries_test #test for bat registers

        table = Table(title='[b]Watch Plant Mode', show_header=False, box=None)
        #table.add_row('[b]Model', f'{inverter.inverter_model.name}, type code 0x{inverter.device_type_code}, module 0x{inverter.inverter_module:04x}')
        table.add_row('[b]---Inverter Details---')
        table.add_row('[b]Inv Serial:',plant.inverter_serial_number,'[b]Dongle Serial:',plant.data_adapter_serial_number)       
        table.add_row('[b]Inverter Model:',f'{inverter.model}','[b]Inv. Gen:',f'{inverter.generation}','[b]Inv. Rating',f'{inverter.inverter_max_power}W')
        table.add_row('[b]Max Export Setting:', f'{inverter.grid_port_max_power_output}W','[b]PV Start V:', f'{inverter.v_pv_start}V')
        table.add_row('[b]Internal DC Busses -','[b]V_p_bus:',f'{inverter.v_p_bus}V','[b]V_n_bus:',f'{inverter.v_n_bus}V','[b]HV Bus?:',f'{inverter.v_highbrigh_bus}V')
        table.add_row('[b]External DC Busses -','[b]Bat Terminals:', f'{str(inverter.v_battery)}V')
        table.add_row('[b]Total work time', f'{inverter.work_time_total}h')
        table.add_row()
        table.add_row('[b]---Inverter State---')
        table.add_row('[b]System mode:', str(inverter.system_mode),'[b]Auto Bat Type:', str(inverter.enable_auto_judge_battery_type)) 
        table.add_row('[b]UPS Fast Switch:', str(inverter.enable_ups_mode),'[b]Is Lithium?:', str(inverter.battery_type)) 
        table.add_row('[b]Eco Mode:', str(inverter.battery_power_mode),'[b]BMS Auto Set:', str(inverter.enable_bms_read))
        table.add_row('[b]DC Discharge', str(inverter.enable_discharge),'[b]Total Bat Cap:', f'{str(inverter.battery_capacity)}AH')
        table.add_row('[b]AC Charge Target:', f'{str(inverter.enable_charge_target)}','[b]Bat Calib.:', f'Step: {str(inverter.battery_calibration_stage)} / 7')
        table.add_row()
        table.add_row('[b]---System Targets---')
        table.add_row('[b]Target SOC:', f'{str(inverter.charge_target_soc)}%')
        table.add_row('[b]Reserve SOC:', f'{str(inverter.battery_soc_reserve)}%')
        table.add_row('[b]Minimum SOC:', f'{str(inverter.battery_discharge_min_power_reserve)}%')       
        table.add_row('[b]Charge Power:',f'{str(inverter.battery_charge_limit)} / 50','[b]Disch. Power:',f'{str(inverter.battery_discharge_limit)} / 50')
        table.add_row()
        table.add_row('[b]---System Temps---')
        table.add_row('[b]Inv. Heatsink','[b]Inv. Charger','[b]Battery temp')
        table.add_row(f'{inverter.temp_inverter_heatsink}°C',f'{inverter.temp_charger}°C',f'{inverter.temp_battery}°C')
        table.add_row()
        table.add_row('[b]---System Power---')
        table.add_row('[b]Demand','[b]Grid In/Out','[b]Inverter Power','[b]EPS Power')
        table.add_row(f'{str(inverter.p_load_demand)}W', f'{str(inverter.p_grid_out)}W', f'{str(inverter.p_inverter_out)}W',f'{str(inverter.p_eps_backup)}W')
        table.add_row()
        table.add_row('[b]---Grid Data---')
        table.add_row('[b]Voltage','[b]Current','[b]Frequency')
        table.add_row(f'{str(inverter.v_ac1)}V', f'{str(inverter.i_ac1)}A', f'{str(inverter.f_ac1)}Hz')
        table.add_row()
        table.add_row('[b]---PV Data---')
        table.add_row('[b]PV String 1','[b]PV String 2')
        table.add_row(f'{str(inverter.p_pv1)}W', f'{str(inverter.p_pv2)}W')
        table.add_row(f'{str(inverter.i_pv1)}A', f'{str(inverter.i_pv2)}A')
        table.add_row(f'{str(inverter.v_pv1)}V', f'{str(inverter.v_pv2)}V')
        #table.add_row('[b]Firmware version', inverter.inverter_firmware_version)
        #table.add_row('[b]System time', inverter.system_time.isoformat(sep=" "))
        #table.add_row('[b]Status', f'{inverter.inverter_status} (fault code: {inverter.fault_code})')
        table.add_row()
        table.add_row('[b]---Battery Data---')
      # table.add_row('[b]Number of batteries', str(len(batteries)))
        #######sort multiple battery addressing out################
        table.add_row('[b]Inverter Combined SOC', f'{str(inverter.battery_percent)}%')
        table.add_row('[b]Battery 1 Raw SOC', f'{str(batteries.soc)}%','[b]Bat Cycles:', f'{str(batteries.num_cycles)}')
        table.add_row('[b]Battery 1 Volt', f'{str(batteries.v_out)}V','[b]Design Cap:', f'{str(batteries.cap_design)}AH')
        table.add_row('[b]Battery 1 Current', f'{str(inverter.i_battery)}A','[b]Calib Cap:', f'{str(batteries.cap_calibrated)}AH')
        table.add_row('[b]Battery 1 Power', f'{str(inverter.p_battery)}W','[b]Remaining Cap:', f'{str(batteries.cap_remaining)}AH')
        table.add_row('[b]UV Limit:', f'{str(inverter.battery_low_voltage_protection_limit)}V','[b]OV Limit:', f'{str(inverter.battery_high_voltage_protection_limit)}V','[b]Bat #Volt Adjust?:', f'{str(inverter.battery_voltage_adjust)}V')
        table.add_row()
        table.add_row('[b]---Bat 1 Cell Data---')
        table.add_row('[b]Cell 1', f'{str(batteries.v_cell_01)}V','[b]Cell 2', f'{str(batteries.v_cell_02)}V','[b]Cell 3', f'{str(batteries.v_cell_03)}V','[b]Cell 4', f'{str(batteries.v_cell_04)}V')
        table.add_row('[b]Cell 5', f'{str(batteries.v_cell_05)}V','[b]Cell 6', f'{str(batteries.v_cell_06)}V','[b]Cell 7', f'{str(batteries.v_cell_07)}V','[b]Cell 8', f'{str(batteries.v_cell_08)}V')
        table.add_row('[b]Cell 9', f'{str(batteries.v_cell_09)}V','[b]Cell 10', f'{str(batteries.v_cell_10)}V','[b]Cell 11', f'{str(batteries.v_cell_11)}V','[b]Cell 12', f'{str(batteries.v_cell_12)}V')
        table.add_row('[b]Cell 13', f'{str(batteries.v_cell_13)}V','[b]Cell 14', f'{str(batteries.v_cell_14)}V','[b]Cell 15', f'{str(batteries.v_cell_15)}V','[b]Cell 16', f'{str(batteries.v_cell_16)}V')
        
        return table

    with Live(auto_refresh=False) as live:
        while True:
            live.update(generate_table(), refresh=True)
            await client.refresh_plant(True, max_batteries=5, retries=3, timeout=1.0)
            await asyncio.sleep(10)

@main.async_command()
async def listen_plant(host: str = '0.0.0.0', port: int = 8899):
    """Only listens to modbus rather than polls for updates and displays key inverter values in CLI as they come in."""
    client = Client(host=host, port=port)
    await client.connect()
    
    def generate_table() -> Table:
        plant = client.plant
        try:
            inverter = plant.inverter
        except KeyError as e:
            return f'awaiting data...'
        ##sort this out for multiple bats
        batteries = plant.batteries_test #test for bat registers

             
        table = Table(title='[b]Listen Plant Mode', show_header=False, box=None)
        #table.add_row('[b]Model', f'{inverter.inverter_model.name}, type code 0x{inverter.device_type_code}, module 0x{inverter.inverter_module:04x}')
        table.add_row('[b]---Inverter Details---')
        table.add_row('[b]Inv Serial:',plant.inverter_serial_number,'[b]Dongle Serial:',plant.data_adapter_serial_number)       
        table.add_row('[b]Inverter Model:',f'{inverter.model}','[b]Inv. Gen:',f'{inverter.generation}','[b]Inv. Rating',f'{inverter.inverter_max_power}W')
        table.add_row('[b]Max Export Setting:', f'{inverter.grid_port_max_power_output}W','[b]PV Start V:', f'{inverter.v_pv_start}V')
        table.add_row('[b]Internal DC Busses -','[b]V_p_bus:',f'{inverter.v_p_bus}V','[b]V_n_bus:',f'{inverter.v_n_bus}V','[b]HV Bus?:',f'{inverter.v_highbrigh_bus}V')
        table.add_row('[b]External DC Busses -','[b]Bat Terminals:', f'{str(inverter.v_battery)}V')
        table.add_row('[b]Total work time', f'{inverter.work_time_total}h')
        table.add_row()
        table.add_row('[b]---Inverter State---')
        table.add_row('[b]System mode:', str(inverter.system_mode),'[b]Auto Bat Type:', str(inverter.enable_auto_judge_battery_type)) 
        table.add_row('[b]UPS Fast Switch:', str(inverter.enable_ups_mode),'[b]Is Lithium?:', str(inverter.battery_type)) 
        table.add_row('[b]Eco Mode:', str(inverter.battery_power_mode),'[b]BMS Auto Set:', str(inverter.enable_bms_read))
        table.add_row('[b]DC Discharge', str(inverter.enable_discharge),'[b]Total Bat Cap:', f'{str(inverter.battery_capacity)}AH')
        table.add_row('[b]AC Charge Target:', f'{str(inverter.enable_charge_target)}','[b]Bat Calib.:', f'Step: {str(inverter.battery_calibration_stage)} / 7')
        table.add_row()
        table.add_row('[b]---System Targets---')
        table.add_row('[b]Target SOC:', f'{str(inverter.charge_target_soc)}%')
        table.add_row('[b]Reserve SOC:', f'{str(inverter.battery_soc_reserve)}%')
        table.add_row('[b]Minimum SOC:', f'{str(inverter.battery_discharge_min_power_reserve)}%')       
        table.add_row('[b]Charge Power:',f'{str(inverter.battery_charge_limit)} / 50','[b]Disch. Power:',f'{str(inverter.battery_discharge_limit)} / 50')
        table.add_row()
        table.add_row('[b]---System Temps---')
        table.add_row('[b]Inv. Heatsink','[b]Inv. Charger','[b]Battery temp')
        table.add_row(f'{inverter.temp_inverter_heatsink}°C',f'{inverter.temp_charger}°C',f'{inverter.temp_battery}°C')
        table.add_row()
        table.add_row('[b]---System Power---')
        table.add_row('[b]Demand','[b]Grid In/Out','[b]Inverter Power','[b]EPS Power')
        table.add_row(f'{str(inverter.p_load_demand)}W', f'{str(inverter.p_grid_out)}W', f'{str(inverter.p_inverter_out)}W',f'{str(inverter.p_eps_backup)}W')
        table.add_row()
        table.add_row('[b]---Grid Data---')
        table.add_row('[b]Voltage','[b]Current','[b]Frequency')
        table.add_row(f'{str(inverter.v_ac1)}V', f'{str(inverter.i_ac1)}A', f'{str(inverter.f_ac1)}Hz')
        table.add_row()
        table.add_row('[b]---PV Data---')
        table.add_row('[b]PV String 1','[b]PV String 2')
        table.add_row(f'{str(inverter.p_pv1)}W', f'{str(inverter.p_pv2)}W')
        table.add_row(f'{str(inverter.i_pv1)}A', f'{str(inverter.i_pv2)}A')
        table.add_row(f'{str(inverter.v_pv1)}V', f'{str(inverter.v_pv2)}V')
        #table.add_row('[b]Firmware version', inverter.inverter_firmware_version)
        #table.add_row('[b]System time', inverter.system_time.isoformat(sep=" "))
        #table.add_row('[b]Status', f'{inverter.inverter_status} (fault code: {inverter.fault_code})')
        table.add_row()
        table.add_row('[b]---Battery Data---')
      # table.add_row('[b]Number of batteries', str(len(batteries)))
        #######sort multiple battery addressing out################
        table.add_row('[b]Inverter Combined SOC', f'{str(inverter.battery_percent)}%')
        table.add_row('[b]Battery 1 Raw SOC', f'{str(batteries.soc)}%','[b]Bat Cycles:', f'{str(batteries.num_cycles)}')
        table.add_row('[b]Battery 1 Volt', f'{str(batteries.v_out)}V','[b]Design Cap:', f'{str(batteries.cap_design)}AH')
        table.add_row('[b]Battery 1 Current', f'{str(inverter.i_battery)}A','[b]Calib Cap:', f'{str(batteries.cap_calibrated)}AH')
        table.add_row('[b]Battery 1 Power', f'{str(inverter.p_battery)}W','[b]Remaining Cap:', f'{str(batteries.cap_remaining)}AH')
        table.add_row('[b]UV Limit:', f'{str(inverter.battery_low_voltage_protection_limit)}V','[b]OV Limit:', f'{str(inverter.battery_high_voltage_protection_limit)}V','[b]Bat Volt Adjust?:', f'{str(inverter.battery_voltage_adjust)}V')
        table.add_row()
        table.add_row('[b]---Bat 1 Cell Data---')
        table.add_row('[b]Cell 1', f'{str(batteries.v_cell_01)}V','[b]Cell 2', f'{str(batteries.v_cell_02)}V','[b]Cell 3', f'{str(batteries.v_cell_03)}V','[b]Cell 4', f'{str(batteries.v_cell_04)}V')
        table.add_row('[b]Cell 5', f'{str(batteries.v_cell_05)}V','[b]Cell 6', f'{str(batteries.v_cell_06)}V','[b]Cell 7', f'{str(batteries.v_cell_07)}V','[b]Cell 8', f'{str(batteries.v_cell_08)}V')
        table.add_row('[b]Cell 9', f'{str(batteries.v_cell_09)}V','[b]Cell 10', f'{str(batteries.v_cell_10)}V','[b]Cell 11', f'{str(batteries.v_cell_11)}V','[b]Cell 12', f'{str(batteries.v_cell_12)}V')
        table.add_row('[b]Cell 13', f'{str(batteries.v_cell_13)}V','[b]Cell 14', f'{str(batteries.v_cell_14)}V','[b]Cell 15', f'{str(batteries.v_cell_15)}V','[b]Cell 16', f'{str(batteries.v_cell_16)}V')
        
        return table

    with Live(auto_refresh=False) as live:
        while True:
            live.update(generate_table(), refresh=True)
            await asyncio.sleep(1.5)

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
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

################### Inverter Settings #####################

@main.async_command()
async def set_ac_charge(val: bool, host: str = '0.0.0.0', port: int = 8899):
    """[TRUE / FALSE] - Enable the battery to charge on AC, depending on the mode and slots set."""
    client = Client(host=host, port=port)
    command = set_enable_charge(val)[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

@main.async_command()
async def eco_on(val: str = 'ECO ENABLED', host: str = '0.0.0.0', port: int = 8899):
    """Set the battery discharge mode to match demand, avoiding importing power from the grid."""
    client = Client(host=host, port=port)
    command = set_discharge_mode_to_match_demand()[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

@main.async_command()
async def eco_off(val: str = 'ECO DISABLED', host: str = '0.0.0.0', port: int = 8899):
    """Disables ECO mode which may export at full power to the grid if export slots are set"""
    client = Client(host=host, port=port)
    command = set_discharge_mode_max_power()[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
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
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

###### Pass Bool Example ######
#@main.async_command()
async def dummy_call2(val: bool, host: str = '0.0.0.0', port: int = 8899):
    """Dummy call that just repeats back commands sent to & received from commands.py for testing"""
    client = Client(host=host, port=port)
    command = set_enable_charge(val)[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
    responder(command,host,port,val)

###### Pass Value Example ######
#@main.async_command()
async def dummy_call3(val, host: str = '0.0.0.0', port: int = 8899):
    """Dummy call that just repeats back commands sent to & received from commands.py for testing"""
    client = Client(host=host, port=port)
    command = set_battery_discharge_limit(val)[0]
    await client.connect()
    await client.execute([command],retries=3, timeout=1.0)
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


asyncio.run(watch_plant2('192.168.2.3',8899))

#if __name__ == "__main__":
#    main()
