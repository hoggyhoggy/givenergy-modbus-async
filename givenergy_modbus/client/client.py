import asyncio
from io import BufferedIOBase
import logging
import socket
from asyncio import Future, Queue, StreamReader, StreamWriter, Task
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..exceptions import (
    CommunicationError,
    ExceptionBase,
)
from ..model.plant import Plant
from ..pdu.framer import ClientFramer, Framer
from ..pdu import (
    HeartbeatRequest,
    TransparentRequest,
    TransparentResponse,
    WriteHoldingRegisterResponse,
)

_logger = logging.getLogger(__name__)


class Client:
    """Asynchronous client utilising long-lived connections to a network device."""

    framer: Framer
    expected_responses: "Dict[int, Future[TransparentResponse]]" = {}
    plant: Plant
    connected = False
    reader: StreamReader
    writer: StreamWriter
    network_consumer_task: Task
    network_producer_task: Task
    recorder: Optional[BufferedIOBase]

    tx_queue: "Queue[Tuple[bytes, Optional[Future]]]"

    def __init__(
        self,
        host: str,
        port: int,
        connect_timeout: float = 2.0,
        recorder: Optional[BufferedIOBase] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.framer = ClientFramer()
        self.plant = Plant()
        self.tx_queue = Queue(maxsize=20)

        # optionally record all received data to a file
        self.recorder = recorder

    async def connect(self) -> None:
        """Connect to the remote host and start background tasks."""
        try:
            connection = asyncio.open_connection(
                host=self.host, port=self.port, flags=socket.TCP_NODELAY
            )
            self.reader, self.writer = await asyncio.wait_for(
                connection, timeout=self.connect_timeout
            )
        except OSError as e:
            raise CommunicationError(
                f"Error connecting to {self.host}:{self.port}"
            ) from e
        self.network_consumer_task = asyncio.create_task(
            self._task_network_consumer(), name="network_consumer"
        )
        self.network_producer_task = asyncio.create_task(
            self._task_network_producer(), name="network_producer"
        )
        self.connected = True
        _logger.info("Connection established to %s:%d", self.host, self.port)

    async def close(self) -> None:
        """Disconnect from the remote host and clean up tasks and queues."""
        if not self.connected:
            return

        _logger.debug("Disconnecting and cleaning up")

        self.connected = False

        if self.tx_queue:
            while not self.tx_queue.empty():
                _, future = self.tx_queue.get_nowait()
                if future:
                    future.cancel()

        if self.network_producer_task:
            self.network_producer_task.cancel()

        if hasattr(self, "writer") and self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            del self.writer

        if self.network_producer_task:
            self.network_consumer_task.cancel()

        if hasattr(self, "reader") and self.reader:
            self.reader.feed_eof()
            self.reader.set_exception(RuntimeError("cancelling"))
            del self.reader

        self.expected_responses = {}

    async def refresh_plant(
        self,
        full_refresh: bool = True,
        max_batteries: int = 5,
        timeout: float = 1.0,
        retries: int = 0,
    ) -> Plant:
        """Refresh data about the Plant."""
        reqs = self.commands.refresh_plant_data(
            full_refresh, self.plant.number_batteries, max_batteries
        )
        await self.execute(reqs, timeout=timeout, retries=retries)

        if full_refresh:
            self.plant.detect_batteries()

        return self.plant

    @property
    def commands(self):
        """Access to the library of commands."""

        # defer import until here to avoid circularity
        from .commands import Commands

        return Commands(self)

    async def watch_plant(
        self,
        handler: Optional[Callable] = None,
        refresh_period: float = 15.0,
        max_batteries: int = 5,
        timeout: float = 1.0,
        retries: int = 0,
        passive: bool = False,
    ):
        """Refresh data about the Plant."""
        await self.connect()
        await self.refresh_plant(True, max_batteries=max_batteries)
        self.plant.detect_batteries()
        while True:
            if handler:
                handler()
            await asyncio.sleep(refresh_period)
            if not passive:
                reqs = self.commands.refresh_plant_data(
                    False, self.plant.number_batteries
                )
                await self.execute(
                    reqs, timeout=timeout, retries=retries, return_exceptions=True
                )

    async def one_shot_command(
        self, requests: Sequence[TransparentRequest], timeout=1.5, retries=0
    ) -> None:
        """Run a single set of requests and return."""
        await self.connect()
        await self.execute(requests, timeout=timeout, retries=retries)

    # The i/o activity is co-ordinated by two background tasks:
    # - the consumer reads from the socket, responds to heartbeat requests,
    #   and sends register updates to the plant
    # - the producer takes requests from tx_queue and writes them to the socket
    #
    # In detail:
    #  the application task calls client.send_request_and_await_response()
    #  - this constructs a couple of 'future' objects, which are used for signalling
    #  - adds the "shape_hash" of the request, with one of the futures, to the expected_responses dict
    #  - adds the request, with the other future, to tx_queue
    #
    #  The producer signals the first future when the request has actually been sent
    #  The consumer signals the second future after a response matching the shape_hash
    #
    #  send_request_and_await_response waits for the futures to be signaled, handling
    #  timeouts and retries as required.  (The timeout doesn't start until the request
    #  has actually been sent.)
    #
    #  Entries don't seem to be removed from expected_responses dict.
    #  Instead, when an entry is reused for a new request, if the existing
    #  future was not signalled, it gets cancelled.
    #
    #  client.execute() takes an array of requests, and creates one coroutine per request,
    #  to run send_request_and_await_response in parallel. They happen in random order ?

    async def _task_network_consumer(self):
        """Task for orchestrating incoming data."""
        while hasattr(self, "reader") and self.reader and not self.reader.at_eof():
            frame = await self.reader.read(300)
            if self.recorder:
                self.recorder.write(frame)
            for message in self.framer.decode(frame):
                _logger.debug("Processing %s", message)
                if isinstance(message, ExceptionBase):
                    _logger.warning(
                        "Expected response never arrived but resulted in exception: %s",
                        message,
                    )
                    continue
                if isinstance(message, HeartbeatRequest):
                    _logger.debug("Responding to HeartbeatRequest")
                    await self.tx_queue.put(
                        (message.expected_response().encode(), None)
                    )
                    if self.recorder:
                        # an opportunity to flush to file, since these arrive regularly
                        self.recorder.flush()
                    continue
                if not isinstance(message, TransparentResponse):
                    _logger.warning(
                        "Received unexpected message type for a client: %s", message
                    )
                    continue
                if isinstance(message, WriteHoldingRegisterResponse):
                    if message.error:
                        _logger.warning("%s", message)
                    else:
                        _logger.info("%s", message)

                # look to see if there's an outstanding request of this "shape",
                # and if so, deliver it (just so it can be marked as done).
                future = self.expected_responses.get(message.shape_hash())

                if future and not future.done():
                    future.set_result(message)

                # and send the message to the plant
                self.plant.update(message)
        _logger.debug(
            "network_consumer reader at EOF, cannot continue, closing connection"
        )
        await self.close()

    async def _task_network_producer(self, tx_message_wait: float = 0.25):
        """Producer loop to transmit queued frames with an appropriate delay."""
        while hasattr(self, "writer") and self.writer and not self.writer.is_closing():
            message, future = await self.tx_queue.get()
            self.writer.write(message)
            await self.writer.drain()
            self.tx_queue.task_done()
            if future:
                future.set_result(True)
            await asyncio.sleep(tx_message_wait)
        _logger.debug(
            "network_producer writer is closing, cannot continue, closing connection"
        )
        await self.close()

    def execute(
        self,
        requests: Sequence[TransparentRequest],
        timeout: float,
        retries: int,
        return_exceptions: bool = False,
    ) -> "Future[List[TransparentResponse | BaseException]]":
        """Helper to perform multiple requests in parallel."""
        return asyncio.gather(
            *[
                self.send_request_and_await_response(
                    m, timeout=timeout, retries=retries
                )
                for m in requests
            ],
            return_exceptions=return_exceptions,
        )

    async def send_request_and_await_response(
        self, request: TransparentRequest, timeout: float, retries: int
    ) -> TransparentResponse:
        """Send a request to the remote, await and return the response."""
        raw_frame = request.encode()

        # the expected response will have the same shape_hash as the outgoing request,
        # so we can use this as the key in our expected_responses table.
        expected_shape_hash = request.shape_hash()

        tries = 0
        while tries <= retries:
            tries += 1
            # cancel any existing incomplete requests on this shape_hash,
            # then store a new 'future' in the expected_responses table.
            existing_response_future = self.expected_responses.get(expected_shape_hash)
            if existing_response_future and not existing_response_future.done():
                _logger.debug(
                    "Cancelling existing in-flight request and replacing: %s", request
                )
                existing_response_future.cancel()
            response_future: Future[TransparentResponse] = (
                asyncio.get_event_loop().create_future()
            )
            self.expected_responses[expected_shape_hash] = response_future

            # queue the frame for transmission, with a 'future' to signal when
            # it has actually been sent, and wait for it to actually get sent.
            frame_sent = asyncio.get_event_loop().create_future()
            await self.tx_queue.put((raw_frame, frame_sent))
            await asyncio.wait_for(
                frame_sent, timeout=self.tx_queue.qsize() + 1
            )  # this should only happen if the producer task is stuck

            _logger.debug("Request sent (attempt %d): %s", tries, request)

            # Now wait for the consumer task to indicate that a response matching
            # our request has arrived.
            try:
                await asyncio.wait_for(response_future, timeout=timeout)
                if response_future.done():
                    response = response_future.result()
                    if tries > 1:
                        _logger.debug("Received %s after %d attempts", response, tries)
                    if response.error:
                        _logger.error("Received error response, retrying: %s", response)
                    else:
                        return response
            except asyncio.TimeoutError:
                pass

            if tries <= retries:
                _logger.debug(
                    "Timeout awaiting response to %s, attempting retry %d of %d",
                    request,
                    tries,
                    retries,
                )

        _logger.warning(
            "Timeout awaiting response to %s after %d tries at %ds, giving up",
            request,
            tries,
            timeout,
        )
        raise asyncio.TimeoutError()
