"""MercuryDetector - top-level control of the MERCURY detector system

This module implements the top-level control interface for the MERCURY detector system

Tim Nicholls, STFC Detector Systems Software Group
"""
import logging

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from mercury.asic.device import MercuryAsicDevice
from .context import SyncContext
from .proxy import MunirProxyContext, GPIBProxyContext


class MercuryDetectorError(Exception):
    """Simple exception class for the MERCURY detector class."""

    pass


class MercuryDetector:
    """
    MERCURY detector class.

    This class implements the top-level control interface to the MERCURY detector system.
    """

    def __init__(self, options):
        """Initialise the detector object.

        :param options: dictionary of configuration options
        """
        # Extract the required configuration settings from the options dict
        emulate_hw = options.get("emulate_hw", False)
        asic_emulator_endpoint = options.get("asic_emulator_endpoint", "")

        self.asic = MercuryAsicDevice(emulate_hw, asic_emulator_endpoint)

        # Define the parameter tree containing register state and client status
        self.parameters = ParameterTree({"status": "hello"})

        # Create a list of other adapters that will be populated later in the initialisation that
        # this adapter needs to communicate with
        self.adapters = {}
        self.needed_adapters = [
            "odin_sequencer",
            "proxy"
        ]

    def initialize(self, adapters):
        """Initialize internal list of registered adapters.

        This method is called by the enclosing adapter with a list of registered adapters in the
        odin-control configuration. This facilitates inter-adapter communication.

        :param adapters: dictionary of currently loaded adapters
        """
        # Iterate through the list of loaded adapters and add any of the needed adapters to
        # to the adapters dict.
        for (name, adapter) in adapters.items():
            if name in self.needed_adapters:
                self.adapters[name] = adapter
                logging.debug(f"Found {name} adapter ({type(adapter).__name__})")

        # Check that all the needed adapters were found, otherwise log a warning
        missing_adapters = set(self.needed_adapters) - set(self.adapters)
        if missing_adapters:
            logging.warning(
                f"Not all needed adapters have been loaded, missing: {', '.join(missing_adapters)}"
            )

        # If a sequencer adapter is loaded, register the appropriate contexts with it
        logging.debug("checking for sequencer presence in loaded adapters: {}".format(self.adapters))
        if "odin_sequencer" in self.adapters:
            logging.debug("Registering contexts with sequencer")
            self.adapters["odin_sequencer"].add_context("detector", self)

            self.sync_context = SyncContext()
            #self.adapters["odin_sequencer"].add_context("asic", self.sync_context)
            self.asic.register_context(self.sync_context)

            if "proxy" in self.adapters:
                logging.debug("Proxy adapter found, assuming munir instance. Adding context to sequencer")
                self.munir_context = MunirProxyContext(self.adapters["proxy"])
                try:
                    self.adapters["odin_sequencer"].add_context("munir", self.munir_context)
                except Exception as e:
                    logging.error(e)

                self.gpib_context = GPIBProxyContext(self.adapters["proxy"])
                try:
                    self.adapters["odin_sequencer"].add_context("gpib", self.gpib_context)
                except Exception as e:
                    logging.error(e)

            else:
                logging.debug("No proxy adapter found to add to sequencer")
        else:
            logging.debug("No sequencer detected")

    async def get(self, path):
        """Get values from the detector paramter tree.

        This method gets values from the parameter tree at the specified path and returns
        them to the calling function in the appropriate structure.

        :param path: path to retreive from the parameter tree
        :return parameter tree data from the specified path
        """
        # result = await self.asic.register_read(0x0, 5)
        try:
            return self.parameters.get(path)
        except ParameterTreeError as e:
            raise MercuryDetectorError(e)

    async def set(self, path, data):
        """Set values in the detector parameter tree.

        This method sets values in the parameter tree (for read-write parameters) at the specified
        path.

        :param path: path in the parameter tree to set data
        :param data: data to set in the parameter tree
        """
        try:
            self.parameters.set(path, data)
        except ParameterTreeError as e:
            raise MercuryDetectorError(e)
