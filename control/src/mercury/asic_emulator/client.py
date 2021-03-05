import asyncio
import logging
import random
import signal

import zmq
import zmq.asyncio
from zmq.utils.strtypes import cast_bytes
import msgpack


class MercuryAsicClient():

    def __init__(self, addr='127.0.0.1', port=5555):

        self.endpoint = f'tcp://{addr}:{port}'
        logging.info(f"Connecting client to emulator at endpoint {self.endpoint}")

        self.ctx = zmq.asyncio.Context.instance()
        self.socket = self.ctx.socket(zmq.DEALER)

        identity = "{:04x}-{:04x}".format(
                    random.randrange(0x10000), random.randrange(0x10000)
                )
        self.socket.setsockopt(zmq.IDENTITY, cast_bytes(identity))
        self.socket.connect(self.endpoint)

    def run(self, loop=None):

        if not loop:
            loop = asyncio.get_event_loop()

        loop.set_exception_handler(self.handle_exception)
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(self.shutdown(loop, signal=s))
            )

        try:
            loop.create_task(self.run_client())
            loop.run_forever()
        finally:
            loop.close()
            logging.info("Emulator shutting down")

    async def run_client(self):

        transactions = [
            [0x80, 0],
            [0x0, 1],
            [0x80, 0],
            [0x0, 3],
            [0x7F, 1, 2, 3, 4, 5],
            [3]
        ]
        while True:
            for msg in transactions:

                logging.info(f"Sending message {msg} to emulator")
                msg_bytes = msgpack.packb(msg)
                await self.socket.send(msg_bytes)

                recvd = await self.socket.recv()
                reply = msgpack.unpackb(recvd)
                logging.info(f"Got reply: {reply}")

                await asyncio.sleep(1.0)

    async def idle(self):
        while True:
            logging.debug(".")
            await asyncio.sleep(1.0)

    def handle_exception(self, loop, context):
        # context["message"] will always be there; but context["exception"] may not
        msg = context.get("exception", context["message"])
        logging.error(f"Caught exception: {msg}")
        logging.info("Shutting down...")
        asyncio.create_task(self.shutdown(loop))

    async def shutdown(self, loop, signal=None):
        """Cleanup tasks tied to the service's shutdown."""
        if signal:
            logging.info(f"Received exit signal {signal.name}...")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

        [task.cancel() for task in tasks]

        logging.info(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()

    async def read(self, transaction):

        print(f"Got read call with {len(transaction)} args: {transaction}")
        transaction[0] |= 0x80
        response = await self.transfer(transaction)
        return response

    async def write(self, transaction):

        print(f"Got write call with {len(transaction)} args: {transaction}")
        response = await self.transfer(transaction)
        return response

    async def transfer(self, transaction):

        send_msg = msgpack.packb(transaction)
        await self.socket.send(send_msg)

        recv_msg = await self.socket.recv()
        response = msgpack.unpackb(recv_msg)
        return response



