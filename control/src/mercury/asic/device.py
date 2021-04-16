"""MercuryAsicDevice - device control class for the MERCURY ASIC.

This class implements the control interface to the MERCURY ASIC. A real ASIC can be controlled via
the SPI register interface or an emulator via client connection.

Tim Nicholls, STFC Detector Systems Software Group
"""

from .registers import RegisterMap
from mercury.asic_emulator.client import MercuryAsicClient

class MercuryAsicDevice():
    """
    MERCURY ASIC device control interface.

    """

    def __init__(self, emulate_asic=False, emulator_endpoint=None):
        """Initialise the ASIC device control.

        param emulate_asic: boolean flag indicating if device should be emulated
        param emulator_endpoint: string endpoint URI for emulator if in use
        """

        if emulate_asic:
            self.device = MercuryAsicClient(emulator_endpoint)
        else:
            raise NotImplementedError("Real ASIC device not implemented yet")

    async def register_read(self, addr, length):

        transaction = [addr] + [0]*length
        response = await self.device.read(transaction)
        return response

    async def register_write(self, addr, *vals):

        transaction = [addr] + list(vals)
        response = await self.device.write(transaction)
        return response