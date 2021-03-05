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

    def __init__(self, options, ioloop=None):

        endpoint = options.get('endpoint', '127.0.0.1:5555')
        log_register_writes = options.get('log_register_writes', False)

        self.register_model = MercuryAsicRegisterModel(self, log_register_writes)
        self.server = EmulatorServer(endpoint, ioloop, self.register_model)

        self.parameters = ParameterTree({
            'status': {
                'connected': (self.server.connected, None),
                'clients': (self.server.clients, None)
            },
            'registers': (self.register_model.registers, None),
        })

    async def get(self, path):
        return self.parameters.get(path)

    async def set(self, path, data):
        return {'path': path, 'data': data}
