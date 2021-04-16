"""MercuryDetectorAdapter - ODIN control adapter for MERCURY detector system

This odin-control async adapter implements an interface to the MERCURY detector.

Tim Nicholls, STFC Detector Systems Software Group
"""
import logging

from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapterResponse, request_types, response_types
from odin.adapters.async_adapter import AsyncApiAdapter

from .detector import MercuryDetector, MercuryDetectorError


class MercuryDetectorAdapter(AsyncApiAdapter):
    """
    MERCURY detector adapter class.

    This class provides the async adapter interface to the MERCURY detector.
    """

    def __init__(self, **kwargs):
        """Initialise the adapter object.

        :param kwargs: keyawrd argument list that is passed to superclass
                       init method to populate options dictionary
        """
        # Initalise super class
        super(MercuryDetectorAdapter, self).__init__(**kwargs)

        # Create ASIC emulator instance, passing in options
        self.detector = MercuryDetector(self.options)

        logging.debug('MercuryDetectorAdapter loaded')

    def initialize(self, adapters):
        """Initialize internal list of registered adapters.

        This method, if present, is called by odin-control once all adapters have been loaded. It
        passes a dict of loaded adapters to facilitate inter-adapter communication.

        :param adapters: dictionary of currently loaded adapters
        """
        self.detector.initialize(adapters)

    @response_types('application/json', default='application/json')
    async def get(self, path, request):
        """Handle an HTTP GET request.

        This async method handles a GET request, passing on the request to the emulator
        and returning the response to the client.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        try:
            response = await self.detector.get(path)
            status_code = 200
        except MercuryDetectorError as e:
            response = {'error': str(e)}
            status_code = 400

        content_type = 'application/json'
        return ApiAdapterResponse(
            response, content_type=content_type, status_code=status_code
        )

    @request_types('application/json', 'application/vnd.odin-native')
    @response_types('application/json', default='application/json')
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
            await self.detector.set(path, data)
            response = await self.detector.get(path)
            status_code = 200
        except MercuryDetectorError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        return ApiAdapterResponse(response, status_code=status_code)
