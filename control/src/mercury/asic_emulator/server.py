import asyncio
import logging

import zmq
import zmq.asyncio
import zmq.utils.monitor
import msgpack

class EmulatorServer():

    def __init__(self, endpoint, ioloop, register_model):

        self.endpoint = endpoint
        self.ioloop = ioloop
        self.register_model = register_model

        self._clients = set()

        logging.info(f"Starting emulator server listening at endpoint {self.endpoint}")
        self.ctx = zmq.asyncio.Context.instance()
        self.socket = self.ctx.socket(zmq.ROUTER)
        self.monitor_socket = self.socket.get_monitor_socket(
            zmq.EVENT_ACCEPTED | zmq.EVENT_DISCONNECTED
        )
        self.socket.bind(self.endpoint)

        if not self.ioloop:
            self.ioloop = asyncio.get_event_loop()
        self.server_task = self.ioloop.create_task(self._run_server())
        self.monitor_task = self.ioloop.create_task(self._run_monitor())

    def connected(self):
        return bool(len(self._clients))

    def clients(self):
        return list(self._clients)

    async def _run_server(self):

        while True:
            recvd_msg = await self.socket.recv_multipart()
            client_id = recvd_msg[0].decode('utf-8')
            try:
                transaction = msgpack.unpackb(recvd_msg[1])
                logging.info(f"Received transaction {transaction} from client ID {client_id}")

                transaction = bytearray(transaction)
                response = self.register_model.process_transaction(transaction)

            except (msgpack.UnpackException, msgpack.UnpackValueError, ValueError) as err:
                logging.error("Failed to unpack client message: %s", err)
                response = transaction

            resp_msg = [client_id.encode('utf-8'), msgpack.packb(response)]
            await self.socket.send_multipart(resp_msg)


    async def _run_monitor(self):

        while True:
            try:
                recvd_msg = await self.monitor_socket.recv_multipart()
                event = zmq.utils.monitor.parse_monitor_message(recvd_msg)
                if event['event'] == zmq.EVENT_ACCEPTED:
                    logging.info(f"New emulator client connection on socket {event['value']}")
                    self._clients.add(event['value'])
                if event['event'] == zmq.EVENT_DISCONNECTED:
                    logging.info(f"Client connection on socket {event['value']} closed")
                    self._clients.discard(event['value'])
            except Exception as err:
                logging.error("Error while handling socket monitoring event: %s", err)