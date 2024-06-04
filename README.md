# GivEnergy Modbus

[![pypi](https://img.shields.io/pypi/v/givenergy-modbus.svg)](https://pypi.org/project/givenergy-modbus/)
[![python](https://img.shields.io/pypi/pyversions/givenergy-modbus.svg)](https://pypi.org/project/givenergy-modbus/)
[![Build Status](https://github.com/dewet22/givenergy-modbus/actions/workflows/dev.yml/badge.svg)](https://github.com/dewet22/givenergy-modbus/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/dewet22/givenergy-modbus/branch/main/graphs/badge.svg)](https://codecov.io/github/dewet22/givenergy-modbus)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A python library to access GivEnergy inverters via Modbus TCP on a local network, with no dependency on the GivEnergy
Cloud.

> ⚠️ This project makes no representations as to its completeness or correctness. You use it at your own risk — if your
> inverter mysteriously explodes because you accidentally set the `BOOMTIME` register or you consume a MWh of
> electricity doing SOC calibration: you **really** are on your own. We make every effort to prevent you from shooting
> yourself in the foot, so as long as you use the client and its exposed methods, you should be perfectly safe.

* Documentation: <https://hoggyhoggy.github.io/givenergy-modbus-async>
* GitHub: <https://hoggyhoggy.github.io/givenergy-modbus-async>
* PyPI: <https://pypi.org/project/givenergy-modbus/>
* Free software: Apache-2.0

## Features

* Reading all registers and decoding them into their representative datatypes
* Writing data to holding registers that are deemed to be safe to set configuration on the inverter

## How to use

Use the provided client to interact with the device over the network, and register caches to build combined state of a
device:

```python
import datetime
from givenergy_modbus.client.client import Client
from givenergy_modbus.model.plant import Plant, Inverter

client = Client(host="192.168.99.99")
await client.connect()

# note - importing givenergy_modbus.client.commands is now deprecated
commands = client.commands

await client.exec(commands.enable_charge_target(80))
# set a charging slot from 00:30 to 04:30
await client.exec(commands.set_charge_slot_1((datetime.time(hour=0, minute=30), datetime.time(hour=4, minute=30)))
# set the inverter to charge when there's excess, and discharge otherwise. it will also respect charging slots.
await client.exec(commands.set_mode_dynamic())

client.refresh_plant(full_refresh=True)
p = client.plant
inverter = p.inverter
assert inverter.serial_number == 'SA1234G567'
assert inverter.model == Model.Hybrid
assert inverter.v_pv1 == 1.4  # V
assert inverter.e_battery_discharge_day == 8.1  # kWh
assert inverter.enable_charge_target

b0 = p.batteries[0]
assert b0.serial_number == 'BG1234G567'
assert b0.v_battery_cell_01 == 3.117
```

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and
the [waynerv/cookiecutter-pypackage](https://github.com/waynerv/cookiecutter-pypackage) project template.
