"""TemperatureMonitorAdapter - ODIN control adapter for MERCURY temperature monitoring

This odin-control adapter implements an interface to monitor temperatures for the HEXITEC-
MHz experimental setup from several reading sources.

It will disable regulators and the peltier control output if a critical condition is
detected.

Joseph Nobes, STFC Detector Systems Software Group
"""
import logging


from tornado.ioloop import IOLoop
from tornado.escape import json_decode
from odin.adapters.adapter import ApiAdapterResponse, request_types, response_types
from odin.adapters.async_adapter import AsyncApiAdapter

from .tempmon import TemperatureMonitor, TemperatureMonitorException


class TemperatureMonitorAdapter(AsyncApiAdapter):
    """
    Temperature Monitor adapter class.
    """

    def __init__(self, **kwargs):
        """Initialise the adapter object.

        :param kwargs: keyawrd argument list that is passed to superclass
                       init method to populate options dictionary
        """
        # Initalise super class
        super(TemperatureMonitorAdapter, self).__init__(**kwargs)

        # Create temperature monitor instance, passing in options
        self.tempmon = TemperatureMonitor(self.options)
        self.monitoring_loop()

        logging.debug("TemperatureMonitorAdapter loaded")

    async def initialize(self, adapters):
        """Initialize internal list of registered adapters.

        This method, if present, is called by odin-control once all adapters have been loaded. It
        passes a dict of loaded adapters to facilitate inter-adapter communication.

        :param adapters: dictionary of currently loaded adapters
        """
        self.tempmon.initialize(adapters)

    def monitoring_loop(self):
        self.tempmon.loop()
        IOLoop.instance().call_later(5, self.monitoring_loop)

    @response_types("application/json", default="application/json")
    async def get(self, path, request):
        """Handle an HTTP GET request.

        This async method handles a GET request, passing on the request to the emulator
        and returning the response to the client.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        try:
            response = await self.tempmon.get(path)
            status_code = 200
        except temperaturemonitorexception as e:
            response = {"error": str(e)}
            status_code = 400

        content_type = "application/json"
        return ApiAdapterResponse(
            response, content_type=content_type, status_code=status_code
        )

    @request_types("application/json", "application/vnd.odin-native")
    @response_types("application/json", default="application/json")
    async def put(self, path, request):
        """Handle an HTTP PUT request.

        This async method handles a PUT request, passing on the request to the emulator
        and returning the response to the client.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        try:
            data = json_decode(request.body)
            await self.tempmon.set(path, data)
            response = await self.tempmon.get(path)
            status_code = 200
        except TemperatureMonitorException as e:
            response = {"error": str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {"error": "Failed to decode PUT request body: {}".format(str(e))}
            status_code = 400

        return ApiAdapterResponse(response, status_code=status_code)
