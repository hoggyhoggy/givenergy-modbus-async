
import logging

from .battery import Battery
from .hvbcu import BCU
from .hvbmu import BMU
from .ems import EMS
from .gateway import Gateway
from .threephase import ThreePhaseInverter

from .inverter import Inverter
from .register import Model
from .register import HR, IR
from .register_cache import (
    RegisterCache,
)
from ..pdu import (
    ClientIncomingMessage,
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
    additional_holding_registers: list[int] = []
    additional_input_registers: list[int] = []
    inverter_serial_number: str = ""
    data_adapter_serial_number: str = ""
    number_batteries: int = 0
    number_bcu: int = 0
    slave_address: int = 0x31
    isHV: bool = True
    device_type: Model

    def __init__(self) -> None:
        if not self.register_caches:
            self.register_caches = {self.slave_address: RegisterCache()}

    def update(self, pdu: ClientIncomingMessage):
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
            slave_address = self.slave_address
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
            self.register_caches[slave_address].update(
                {HR(k): v for k, v in pdu.to_dict().items()}
            )
        elif isinstance(pdu, ReadInputRegistersResponse):
            self.register_caches[slave_address].update(
                {IR(k): v for k, v in pdu.to_dict().items()}
            )
        elif isinstance(pdu, WriteHoldingRegisterResponse):
            if pdu.register == 0:
                _logger.warning(f"Ignoring, likely corrupt: {pdu}")
            else:
                self.register_caches[slave_address].update(
                    {HR(pdu.register): pdu.value}
                )

    def detect_batteries(self) -> None:
        """Determine the number of batteries based on whether the register data is valid.

        Since we attempt to decode register data in the process, it's possible for an
        exception to be raised.
        """
        if self.inverter.model==Model.EMS or self.inverter.model==Model.GATEWAY:
            self.number_batteries=0
            return
        if self.isHV:
            self.number_batteries=BCU(self.register_caches[0x70]).get('number_of_module')
        else:
            i = 0
            for i in range(6):
                try:
                        assert Battery(self.register_caches[i + 0x32]).is_valid()
                except (KeyError, AssertionError):
                    break
            self.number_batteries = i

        #if self.isHV:
        #    i = 0
        #    for i in range(6):
        #        try:
        #            assert BCU(self.register_caches[i + 0x70]).is_valid()
        #        except (KeyError, AssertionError):
        #            break
        #    self.number_bcu=i

    @property
    def inverter(self) -> Inverter:     #Would an AIO Class make sense here?
        """Return Inverter model for the Plant."""
        if hex(self.register_caches[self.slave_address][HR(0)])[2:3]=="4":
            return ThreePhaseInverter(self.register_caches[self.slave_address])
        elif hex(self.register_caches[self.slave_address][HR(0)])[2:3] in ("2","3","8"):
            return Inverter(self.register_caches[self.slave_address])
    
#    @property
#    def threephaseinverter(self) -> Inverter:
#        """Return 3ph Inverter model for the Plant."""
#        return ThreePhaseInverter(self.register_caches[self.slave_address])
    
    @property
    def ems(self) -> EMS:
        """Return EMS model for the Plant."""
        if hex(self.register_caches[self.slave_address][HR(0)])[2:3]=="5":
            return EMS(self.register_caches[self.slave_address])
    
    @property
    def gateway(self) -> Gateway:
        """Return Gateway model for the Plant."""
        if hex(self.register_caches[self.slave_address][HR(0)])[2:3]=="7":
            return Gateway(self.register_caches[self.slave_address])

    @property
    def batteries(self) -> list[Battery]:
        """Return LV Battery models for the Plant."""
        if self.isHV:
            return [
                BMU(self.register_caches[i + 0x50])
                for i in range(self.number_batteries)
            ]
        else:
            return [
                Battery(self.register_caches[i + 0x32])
                for i in range(self.number_batteries)
            ]
        
    @property
    def bcu(self) -> list[BCU]:
        """Return HV Battery models for the Plant."""
        if self.isHV:
            return [    
                BCU(self.register_caches[0x70])
            ]