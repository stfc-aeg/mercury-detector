""" TemperatureMonitor - top-level control of the MERCURY detector system

This class implements system-wide temperature monitoring (both via carrier
devices and GPIB instruments) and control to allow reaction to detected
critical conditions.

Joseph Nobes, STFC Detector Systems Software Group
"""
import logging
from enum import Enum

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from ..detector.proxy import GPIBProxyContext

class TemperatureMonitorException(Exception):
    """Simple exception class for the Temperature Monitor class."""

    pass


class MonState(Enum):
    MONITORING = 1
    TRIGGERED = 2


class TemperatureMonitor:
    """
    Temperature Monitor class.

    This class implements system-wide temperature monitoring (both via carrier
    devices and GPIB instruments) and control to allow reaction to detected
    critical conditions.
    """

    def __init__(self, options):
        """Initialise the detector object.

        :param options: dictionary of configuration options
        """
        # Extract the required configuration settings from the options dict
        self._autoready = bool(options.get("tempmon_autoready_noreading", False))
        logging.debug('autoready: {}, type: {}'.format(self._autoready, type(self._autoready)))
        self._critical_temperature = options.get("critical_temperature", 50)
        gpib_peltier_endpoint = options.get("gpib_peltier_endpoint", "")
        carrier_endpoint = options.get("carrier_endpoint", "")

        self._status = "Init"
        self._reading = None
        self._source = "No source yet"

        # Define the parameter tree containing register state and client status
        self.parameters = ParameterTree({
            "status": (lambda: self._status, None, {"description":"Status / reason for disabling"}),
            "reading_source": (lambda: self._source, None, {"description":"Source of latest temperature reading"}),
            "reading": (lambda: self._reading, None, {"description":"Latest temperature reading"})
            })

        self.STATE = MonState.MONITORING

        # Create a list of other adapters that will be populated later in the initialisation that
        # this adapter needs to communicate with
        self.adapters = {}
        self.needed_adapters = ["carrier", "proxy"]

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

        # If a proxy adapter which contains GPIB is loaded, use it for the peltier
        logging.debug("checking for gpib presence in proxy adapter (if present): {}".format(self.adapters))
        if "proxy" in self.adapters:
            logging.debug("Proxy adapter found, searching for GPIB")
            # Is this needed if I have already loaded it into detector?
            #self._gpib_context = None
            self._gpib_context = GPIBProxyContext(self.adapters["proxy"])
        else:
            logging.debug("No proxy adapter found")

    def read_system_temperature(self):
        """ Step through various temperature sources for a valid reading.

        Several tempeature sources are tried in order of preference. Whether each is available
        depends on various conditions. The ASIC diode is the best source; it reads directly from
        inside the device. Both PT100s are in the cooling block.
        """

        try:
            """ Attempt to read the ASIC Diode. This utilises the LTC2986, which will only be
            available when the regualtors are enabled. This provides the most accurate indication
            of the ASIC temperature."""
            temp = self.adapters['carrier'].carrier._asic_temp
            if temp is None: raise TemperatureMonitorException('Temp cannot be None')

            self._reading = temp
            self._source = 'ASIC Diode'
            return temp
        except Exception as e:
            logging.debug("Failed to read ASIC diode temperature, LTC may be disconnected: {}".format(e))

        try:
            raise Exception('Not implemented')
            temp = self._gpib_context.get_peltier_measurement()
            if temp is None: raise TemperatureMonitorException('Temp cannot be None')

            self._reading = temp
            self._source = 'Peltier'
            return temp
        except Exception as e:
            logging.debug("Failed to read peltier temperature: {}".format(e))

        try:
            temp = self.adapters['carrier'].carrier._pt100_temp
            if temp is None: raise TemperatureMonitorException('Temp cannot be None')

            self._reading = temp
            self._source = 'PT100'
            return temp
        except Exception as e:
            logging.debug("Failed to read PT100 temperature, LTC may be disconnected: {}".format(e))

        try:
            temp = self.adapters['carrier'].carrier.get_ambient_temperature()
            if temp is None:
                logging.debug('BME280: {}'.format( self.adapters['carrier'].carrier._bme280))
                raise TemperatureMonitorException('Temp cannot be None')

            self._reading = temp
            self._source = 'BME280'
            return temp
        except Exception as e:
            logging.debug("Failed to read ambient temperature: {}".format(e))

        logging.warning('Temperature monitor failed to get a temperature from any source')
        self._reading = None
        self._source = "No source found"
        return None

    def handle_temperature(self, temperature):
        if temperature is None:
            if self._autoready:
                """ If autoready is enabled, the system will allow the regulators to
                be enabled in the event that no temperature is read."""
                logging.debug('System has enabled autoready; will allow regulators to be switched despite no temperature reading')
                self.enable_system('autoready: system will enable with no temperature source')
            else:
                self.disable_system('No reading')

        elif temperature >= self._critical_temperature:
            self.disable_system('Critical temperature: {}C (limit: {}C)'.format(
                temperature, self._critical_temperature))

        else:
            """ Temperature should be OK"""
            self.enable_system()

    def enable_system(self, reason=''):
        self._state = MonState.MONITORING
        self._status = 'OK; ' + reason
        #TODO enable the system

    def disable_system(self, reason='No reason given'):
        self._state = MonState.TRIGGERED
        self._status = 'Disabled; ' + reason
        logging.warning('System disabled by temperature monitor: {}'.format(reason))
        #TODO disable the system

    def loop(self):
        temp = self.read_system_temperature()
        if temp is not None:
            logging.debug('Successfully read temperature from {}: {}C'.format(
                self._source, self._reading))

        self.handle_temperature(temp)

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
            raise TemperatureMonitorException(e)

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
            raise TemperatureMonitorException(e)
