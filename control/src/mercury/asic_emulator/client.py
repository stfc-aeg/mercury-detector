"""MercuryAsicClient - client class for communicating with the MERCURY ASIC emulator.

This class implements a client that communicates with the MERCURY ASIC emulator, simulating the
SPI transaction interface that the real ASIC will present to the control system. The connection
is made via a ZeroMQ channel, with register read/write accesses encoded with msgpack.

Tim Nicholls, STFC Detector Systems Software Group
"""
import asyncio
import logging
import random
import signal

import zmq
import zmq.asyncio
from zmq.utils.strtypes import cast_bytes
import msgpack

from .register_model import MercuryAsicRegisterModel


class MercuryAsicClient():
    """
    Mercury ASIC client class.

    This class provides a client for communicating with the MERCURY ASIC emulator via a ZeroMQ
    channel. The client can either be run standalone, sending and receiving a fixed set of
    transaction as a basic test, or used by other code to read/write communication as necessary.
    """

    def __init__(self, endpoint='tcp://127.0.0.1:5555'):
        """Initialise the client object.

        :param endpoint: string endpoint URI of the emulator server (default tcp://127.0.0.1:5555)
        """
        self.endpoint = endpoint
        logging.info(f"Connecting client to emulator at endpoint {self.endpoint}")

        # Create a ZeroMQ async context and socket
        self.ctx = zmq.asyncio.Context.instance()
        self.socket = self.ctx.socket(zmq.DEALER)

        # As this is a dealer socket, define a randomised client ID and set on the socket
        identity = "{:04x}-{:04x}".format(
                    random.randrange(0x10000), random.randrange(0x10000)
                )
        self.socket.setsockopt(zmq.IDENTITY, cast_bytes(identity))

        # Connect the socket to the server
        self.socket.connect(self.endpoint)

    async def read(self, transaction):
        """Execute an ASIC register read transaction.

        This method sends a register read transaction to the ASIC emulator. The transaction
        is structured in analogy to the equivalent full-duplex SPI transaction, with the register
        address in the first byte with the RW bit set to 1 and then additional bytes implying the
        number of registers to read. For example, to read three registers from a specified starting
        address, the total length would be four.

        :param transaction: bytearray of the appropriate length (read length + 1 address byte)
        :return bytearray response from the emulator
        """
        logging.debug(f"Executing read transaction with {len(transaction)} args: {transaction}")

        # Set the read/write bit in the address byte
        transaction[0] |= MercuryAsicRegisterModel.REGISTER_RW_MASK

        # Send the transaction and return the response
        response = await self.transfer(transaction)
        return response

    async def write(self, transaction):
        """Execute an ASIC register write transaction.

        This method sends a register write transaction to the ASIC emulator. The transaction is
        structued in analogy to the equivalent full-duplex SPI transaction, with the register
        address in the first byte (with no RW bit set) and then additional bytes containing the
        values of the registers at consecutive addresses to be written.

        :param transaction: bytearray of the appropriate length (1 address byte + register values)
        :return bytearray response from the emulator
        """
        logging.debug(f"Executing write transaction with {len(transaction)} args: {transaction}")

        # Ensure the read/write bit is cleared in the address byte
        transaction[0] &= MercuryAsicRegisterModel.REGISTER_ADDR_MASK

        # Send the transaction and return the response
        response = await self.transfer(transaction)
        return response

    async def transfer(self, transaction):
        """Transfer an ASIC register transaction to the emulator.

        This method transfers an encoded ASIC register transaction to the emulator. The
        transaction is encoded with msgpack then transmitted on the ZeroMQ channel. A response is
        then awaited, unpacked and returned.

        :param transaction: bytearray of the register transaction to transfer
        :return response: bytearray response from the emulator
        """
        # Pack the transaction and send on the socket
        send_msg = msgpack.packb(transaction)
        await self.socket.send(send_msg)

        # Receive the response, unpack it and return
        recv_msg = await self.socket.recv()
        response = msgpack.unpackb(recv_msg)
        return response

    def test(self, ioloop=None):
        """
        Test the client-server communication.

        This method tests the emulator client-server connection by looping indefinitely and
        sending a set of legal and illegal transactions to the server.

        :param: ioloop: asyncio loop to run the client in (default None = create a new loop)
        """
        # Get a new ioloop if none specified
        if not ioloop:
            ioloop = asyncio.get_event_loop()

        # Add an exception handler to the loop and a signal handler to the process to allow for
        # clean termination of the test loop
        ioloop.set_exception_handler(self.handle_exception)
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            ioloop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(self.shutdown(ioloop, signal=s))
            )

        async def test_loop():
            """Inner async function for the client test loop."""
            # Define a set of transactions to loop over
            transactions = [
                [0x80, 0], [0x0, 1], [0x80, 0], [0x0, 3], [0x7F, 1, 2, 3, 4, 5], [3]
            ]

            # Loop forever, sending and recieving transactions
            while True:
                for transaction in transactions:
                    response = await self.transfer(transaction)
                    logging.info(f"Got response: {response}")
                    await asyncio.sleep(1.0)

        # Create a task on the ioloop for the test loop and run it
        try:
            ioloop.create_task(test_loop())
            ioloop.run_forever()
        finally:
            ioloop.close()
            logging.info("Emulator shutting down")

    def handle_exception(self, ioloop, context):
        """Handle exceptions thrown by tasks on the ioloop.

        This method, when registered with the asyncio ioloop, handles exceptions thrown by
        async tasks running on the loop. When this happens the exception is reported and the
        shutdown function called to clean up all running tasks.

        :param ioloop: async ioloop in which the exception occurred
        :param context: dict containing details of the exception context
        """
        # Get information about the exception from the context:
        # context["message"] will always be there; but context["exception"] may not
        msg = context.get("exception", context["message"])

        # Log an appropriate error message
        logging.error(f"Caught exception: {msg}")
        logging.info("Shutting down...")

        # Start the shutdown task to gracefully shutdown any current tasks on the loop
        asyncio.create_task(self.shutdown(ioloop))

    async def shutdown(self, ioloop, signal=None):
        """Shut down all currently running tasks.

        This async method cleanly shuts down all aysncio tasks currently running. It can either be
        bound to a standard signal handler (when wrapped in a task) or called by an asyncio
        exception handler. Once all tasks are stopped, the specified ioloop is terminated.

        :param ioloop: asyncio ioloop to terminate
        :param signal: signal invoking the handler, if any
        """
        # Log a message if this was invoked by a signal handler
        if signal:
            logging.info(f"Received exit signal {signal.name}...")

        # Get a list of all current aysncio tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

        # Cancel the tasks
        logging.info(f"Cancelling {len(tasks)} outstanding tasks")
        [task.cancel() for task in tasks]

        # Wait for the tasks to complete and then stop the ioloop
        await asyncio.gather(*tasks, return_exceptions=True)
        ioloop.stop()
