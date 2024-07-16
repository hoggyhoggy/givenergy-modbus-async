import logging

from .battery import Battery
from .inverter import Inverter
from .register import HR
from .register_cache import (
    RegisterCache,
)
from ..pdu import (
    BasePDU,
    NullResponse,
    ReadHoldingRegistersResponse,
    ReadInputRegistersResponse,
    TransparentResponse,
    WriteHoldingRegisterResponse,
)

_logger = logging.getLogger(__name__)


class Plant:
    """Representation of a complete GivEnergy plant."""

    register_caches: dict[int, RegisterCache] = {}
    inverter_serial_number: str
    data_adapter_serial_number: str = ""
    number_batteries: int = 0

    def __init__(self, inverter_serial_number: str = "", register_caches=None) -> None:
        self.inverter_serial_number = inverter_serial_number
        if not register_caches:
            register_caches = {0x32: RegisterCache()}
        self.register_caches = register_caches

    def update(self, pdu: BasePDU):
        """Update the Plant state from a PDU message."""
        if not isinstance(pdu, TransparentResponse):
            _logger.debug(f"Ignoring non-Transparent response {pdu}")
            return
        if isinstance(pdu, NullResponse):
            _logger.debug(f"Ignoring Null response {pdu}")
            return
        if pdu.error:
            _logger.debug(f"Ignoring error response {pdu}")
            return
        _logger.debug(f"Handling {pdu}")

        if pdu.slave_address in (0x11, 0x00):
            # rewrite cloud and mobile app responses to "normal" inverter address
            slave_address = 0x32
        else:
            slave_address = pdu.slave_address

        if slave_address not in self.register_caches:
            _logger.debug(
                f"First time encountering slave address 0x{slave_address:02x}"
            )
            self.register_caches[slave_address] = RegisterCache()

        self.inverter_serial_number = pdu.inverter_serial_number
        self.data_adapter_serial_number = pdu.data_adapter_serial_number

        if isinstance(pdu, ReadHoldingRegistersResponse):
            self.register_caches[slave_address].update(pdu.enumerate())
        elif isinstance(pdu, ReadInputRegistersResponse):
            self.register_caches[slave_address].update(pdu.enumerate())
        elif isinstance(pdu, WriteHoldingRegisterResponse):
            if pdu.register == 0:
                _logger.warning(f"Ignoring, likely corrupt: {pdu}")
            else:
                self.register_caches[slave_address][HR(pdu.register)] = pdu.value

    def detect_batteries(self) -> None:
        """Determine the number of batteries based on whether the register data is valid.

        Since we attempt to decode register data in the process, it's possible for an
        exception to be raised.
        """
        i = 0
        for i in range(6):
            try:
                assert Battery(self.register_caches[i + 0x32]).is_valid()
            except (KeyError, AssertionError):
                break
        _logger.debug("Updating connected battery count to %d", i)
        self.number_batteries = i

    @property
    def inverter(self) -> Inverter:
        """Return Inverter model for the Plant."""
        return Inverter(self.register_caches[0x32])

    @property
    def batteries(self) -> list[Battery]:
        """Return Battery models for the Plant."""
        return [
            Battery(self.register_caches[i + 0x32])
            for i in range(self.number_batteries)
        ]
