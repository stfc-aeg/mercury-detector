"""EmulatorServer - ZeroMQ-based server for MERCURY ASIC emulation.

This module implements a server for the MERCURY ASIC emulation, handling
client connections via ZeroMQ which emulate SPI register transactions. Transactions
are encoded with msgpack and passed to the underlying register module for processing.

Tim Nicholls, STFC Detector Systems Software Group.
"""
import asyncio
import logging

import zmq
import zmq.asyncio
import zmq.utils.monitor
import msgpack


class EmulatorServer():
    """
    MERCURY ASIC emulator server class.

    The class implements the MERCURY ASIC emulator server.
    """

    def __init__(self, endpoint, ioloop, register_model):
        """Intialize the EmulatorServer object.

        :param endpoint: ZMQ server endpoint URI
        :param ioloop: ayncio ioloop to run server in, or None if to be created
        :param register_model: MercuryAsicRegisterModel instance
        """
        # Store arguments for use
        self.endpoint = endpoint
        self.ioloop = ioloop
        self.register_model = register_model

        # Initialise empty set of connected clients
        self._clients = set()

        # Create the ZeroMQ aysnc context, server and monitor sockets and bind the server socket
        logging.info(f"Starting emulator server listening at endpoint {self.endpoint}")
        self.ctx = zmq.asyncio.Context.instance()
        self.socket = self.ctx.socket(zmq.ROUTER)
        self.monitor_socket = self.socket.get_monitor_socket(
            zmq.EVENT_ACCEPTED | zmq.EVENT_DISCONNECTED
        )
        self.socket.bind(self.endpoint)

        # There no ioloop was passed, get one
        if not self.ioloop:
            self.ioloop = asyncio.get_event_loop()

        # Start the server and monitor tasks on the ioloop
        self.server_task = self.ioloop.create_task(self._run_server())
        self.monitor_task = self.ioloop.create_task(self._run_monitor())

    def connected(self):
        """Return true if one or more clients are connected."""
        return bool(len(self._clients))

    def clients(self):
        """Return a list of connected clients."""
        return list(self._clients)

    async def _run_server(self):
        """Run the server socket task loop."""
        while True:

            # Wait for a message to be received on the socket
            recvd_msg = await self.socket.recv_multipart()

            # Extract the router-dealer client ID from the message
            client_id = recvd_msg[0].decode('utf-8')

            try:

                # Decode the transaction
                transaction = msgpack.unpackb(recvd_msg[1])
                logging.info(f"Received transaction {transaction} from client ID {client_id}")

                # Convert transaction to a bytearray in analogy to an SPI transactio and pass
                # to the emulator register model for processing
                transaction = bytearray(transaction)
                response = self.register_model.process_transaction(transaction)

            except (msgpack.UnpackException, msgpack.UnpackValueError, ValueError) as err:
                # Handle transaction decoding errors - in the case of an error, return the
                # transaction unprocessed.
                logging.error("Failed to unpack client message: %s", err)
                response = transaction

            # Encode the response to the client and transmit on the socket
            resp_msg = [client_id.encode('utf-8'), msgpack.packb(response)]
            await self.socket.send_multipart(resp_msg)

    async def _run_monitor(self):
        """Run the server monitor socket task loop."""
        while True:
            try:

                # Wait for socket monitor events to be received
                recvd_msg = await self.monitor_socket.recv_multipart()

                # Decode the monitor message
                event = zmq.utils.monitor.parse_monitor_message(recvd_msg)

                # Handle the event depending on type, adding or removing the socket from
                # the currently connected client set accordingly
                if event['event'] == zmq.EVENT_ACCEPTED:
                    logging.info(f"New emulator client connection on socket {event['value']}")
                    self._clients.add(event['value'])
                if event['event'] == zmq.EVENT_DISCONNECTED:
                    logging.info(f"Client connection on socket {event['value']} closed")
                    self._clients.discard(event['value'])

            except Exception as err:
                logging.error("Error while handling socket monitoring event: %s", err)
