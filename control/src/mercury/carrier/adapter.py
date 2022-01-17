from .Carrier import Carrier, Carrier_Interface

from tornado.ioloop import IOLoop
from tornado.escape import json_decode
from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types, wants_metadata
from odin._version import get_versions
from odin.adapters.parameter_tree import ParameterTreeError

import logging

class CarrierAdapter(ApiAdapter):

    def initialize(self, adapters):
        """Initialize the ApiAdapter after it has been registered by the API Route.
        This is an abstract implementation of the initialize mechinism that allows
        an adapter to receive a list of loaded adapters, for Inter-adapter communication.

        :param adapters: a dictionary of the adapters loaded by the API route.
        """

        logging.debug("CarrierAdapter initialize called to link sequencer context")
        # Receive and store adapters
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)


        # Add the sequencer context
        logging.debug("Adding context to odin_sequencer")
        sequencer_adapter = self.adapters['odin_sequencer']
        try:
            current_object = sequencer_adapter
            current_class = "sequencer adapter"
            current_function = "add_context"
            getattr(current_object, current_function)

            current_object = sequencer_adapter.command_sequencer
            current_class = "sequencer adapter command sequencer"
            current_function = "_add_context"
            getattr(current_object, current_function)

            current_object = sequencer_adapter.command_sequencer.manager
            current_class = "sequencer adapter manager"
            current_function = "add_context"
            getattr(current_object, current_function)
        except AttributeError:
            logging.debug(
                    "{} object has no {}() function, dir:"
                    "\n\t{}".format(current_class, current_function, dir(current_object)))
            logging.debug("type: {}, self: {}".format(type(current_object), current_object))
            exit()
        logging.debug("All objects had valid add_context when checked, proceeding...")

        self.adapters['odin_sequencer'].add_context('carrier', self.carrier)

        # Temporarily start the test sequence
        logging.debug("Starting the test sequence...")
        logging.debug("dir of odin_sequencer adapter: {}".format(dir(self.adapters['odin_sequencer'])))
        #self.adapters['odin_sequencer'].ff_channel_toggle_test(1, 5)

        logging.debug("THIS IS THE END OF CARRIER ADAPTER INIT")

    def __init__(self, **kwargs):

        # Init superclass
        super(CarrierAdapter, self).__init__(**kwargs)

        # Parse options
        si_config_location = self.options.get('clk_config_location')
        si_filename = self.options.get('clk_default_config_filename')

        _interface_definition_test = Carrier_Interface(
                i2c_device_bus=1,
                spidev_id_mercury=(0, 1),
                spidev_id_ltc=(1, 0),
                spidev_id_max=(1, 1),
                pin_firefly_1=6,
                pin_firefly_2=7,            # NC
                pin_nRead_int=3,            # Moved here
                pin_sync=0,
                pin_sync_sel=8,             # NC, moved here
                pin_asic_nrst=10,           # NC, moved here
                pin_vreg_en=11,
        )

        _interface_definition_ribbon = Carrier_Interface(
                i2c_device_bus=1,
                spidev_id_mercury=(0, 1),
                spidev_id_ltc=(1, 0),
                spidev_id_max=(1, 1),
                pin_firefly_1=6,
                pin_firefly_2=7,
                pin_nRead_int=11,
                pin_sync=0,
                pin_sync_sel=10,
                pin_asic_nrst=3,
                pin_vreg_en=2,
        )

        use_iv = True

        self.carrier = Carrier(si_config_location, si_filename, use_iv, interface_definition=_interface_definition_ribbon)

        # Call self-repeating loops for first time
        self.power_update_interval = float(1.0)
        self.power_update_loop()
        self.firefly_update_interval = float(1.0)
        self.firefly_update_loop()

    def power_update_loop(self):
        """
        Repeatedly monitor the power of the three buses. This can be done even with
        the enable signal off, since the PAC1921s are powererd via VDD3v3.
        """
        self.carrier.sync_power_readings()

        # Schedule the update loop to run in the IOLoop instance again after appropriate
        # interval
        IOLoop.instance().call_later(self.power_update_interval, self.power_update_loop)

    def firefly_update_loop(self):
        self.carrier.sync_firefly_readings()

        # Schedule the update loop to run in the IOLoop instance again after appropriate
        # interval
        IOLoop.instance().call_later(self.firefly_update_interval, self.firefly_update_loop)


    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.
        This method handles an HTTP GET request, returning a JSON response.
        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        if not self.carrier._POWER_CYCLING:     # TODO find a neater way to do this
            try:
                response = self.carrier.get(path, wants_metadata(request))
                status_code = 200
            except ParameterTreeError as e:
                response = {'error': str(e)}
                status_code = 400

            content_type = 'application/json'

            return ApiAdapterResponse(response, content_type=content_type,
                                      status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.
        This method handles an HTTP PUT request, returning a JSON response.
        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """

        if not self.carrier._POWER_CYCLING:     # TODO find a neater way to do this
            content_type = 'application/json'
            data=0
            try:
                data = json_decode(request.body)
                print("path, data: ", path, ", ", data)
                self.carrier.set(path, data)
                response = self.carrier.get(path)
                status_code = 200
            #tempexcept CarrierError as e:
            #temp    response = {'error': str(e)}
            #temp    status_code = 400
            except (TypeError, ValueError) as e:
                response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
                status_code = 400

            logging.debug(data)
            #logging.debug(response)

            return ApiAdapterResponse(response, content_type=content_type,
                                      status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.
        This method handles an HTTP DELETE request, returning a JSON response.
        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        if not self.carrier._POWER_CYCLING:     # TODO find a neater way to do this
            response = 'CarrierAdapter: DELETE on path {}'.format(path)
            status_code = 200

            logging.debug(response)

            return ApiAdapterResponse(response, status_code=status_code)
