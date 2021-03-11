"""MercuryAsicEmulator - emulation of the MERCURY ASIC.

This module implements emulation of the MERCURY ASIC, retaining a model of the
register state and responding to register transactions from clients.

Tim Nicholls, STFC Detector Systems Software Group
"""
import logging

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from .register_model import MercuryAsicRegisterModel
from .server import EmulatorServer


class MercuryAsicEmulatorError(Exception):
    """Simple exception class for the MERCURY ASIC emulator."""

    pass


class MercuryAsicEmulator():
    """
    MERCURY ASIC emulator class.

    This class implements the MERCURY ASIC emulator, handling client transaction requests
    sent to a ZeroMQ server and processing those transactions through a register model. The
    emulator holds a parameter tree representing the current state of the reigsters and
    connected clients for access by an adapter.
    """

    def __init__(self, options, ioloop=None):
        """Initialise the emulator object.

        :param options: dictionary of emulator configuration options
        """
        # Extract the required configuration settings from the options dict
        endpoint = options.get('endpoint', '127.0.0.1:5555')
        log_register_writes = options.get('log_register_writes', False)

        # Create the ASIC register model
        self.register_model = MercuryAsicRegisterModel(self, log_register_writes)

        # Create the emulator server
        self.server = EmulatorServer(endpoint, ioloop, self.register_model)

        # Define the parameter tree containing register state and client status
        self.parameters = ParameterTree({
            'status': {
                'connected': (self.server.connected, None),
                'clients': (self.server.clients, None)
            },
            'registers': (self.register_model.registers, None),
        })

    async def get(self, path):
        """Get values from the emulator paramter tree.

        This method gets values from the parameter tree at the specified path and returns
        them to the calling function in the appropriate structure.

        :param path: path to retreive from the parameter tree
        :return parameter tree data from the specified path
        """
        try:
            return self.parameters.get(path)
        except ParameterTreeError as e:
            raise MercuryAsicEmulatorError(e)

    async def set(self, path, data):
        """Set values in the emulator parameter tree.

        This method sets values in the parameter tree (for read-write parameters) at the specified
        path.

        :param path: path in the parameter tree to set data
        :param data: data to set in the parameter tree
        """
        try:
            self.parameters.set(path, data)
        except ParameterTreeError as e:
            raise MercuryAsicEmulatorError(e)
