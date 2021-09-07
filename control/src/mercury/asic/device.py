"""MercuryAsicDevice - device control class for the MERCURY ASIC.

This class implements the control interface to the MERCURY ASIC. A real ASIC can be controlled via
the SPI register interface or an emulator via client connection.

Tim Nicholls, STFC Detector Systems Software Group
"""

from .registers import RegisterMap
from mercury.asic_emulator.client import MercuryAsicClient


class MercuryAsicDevice:
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

    def register_context(self, context):
        """Register device control with context.

        This method registers the device control read/write methods with the
        context supplied as a parameter, e.g. for use in a command sequencer.
        The entries in the register map are also added to the context so that
        they are accessible therein.

        param context: context to add methods and registers to
        """

        context.register_read = self.register_read
        context.register_write = self.register_write

        for register in RegisterMap:
            context.setattr(register.name, register.value, wrap=False)

    async def register_read(self, addr, length):
        """Read ASIC device registers.

        This async method reads one or more registers from the ASIC device at
        a specified address.

        param addr: start address for reading
        param length: number of registers to read
        return: output of the device read transaction
        """
        transaction = [addr] + [0] * length
        response = await self.device.read(transaction)
        return response

    async def register_write(self, addr, *vals):
        """Write ASIC device registers.

        This async method writes one or more registers to the ASIC device at
        a specified address.

        param addr: start address for writing
        param vals: values to write to registers
        return: output of the device write transaction
        """
        transaction = [addr] + list(vals)
        response = await self.device.write(transaction)
        return response
