"""
Top-level package for GivEnergy Modbus.

This gives direct access to your GivEnergy inverter over
the local network, without requiring the use of the cloud.
**All use is at your own risk.** It is *not* supported by GivEnergy
themselves.

An application will typically use the *client* and *model* modules - the
*pdu* package is just used for encoding and decoding modbus messages, and
shouldn't be needed directly.
"""

__author__ = """Dewet Diener"""
__email__ = 'givenergy-modbus@dewet.org'
__version__ = '1.0.0'
