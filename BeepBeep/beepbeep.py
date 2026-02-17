import json
from pathlib import Path

import typing

import asyncio
from asyncio import Event
from networking import generate_websocket, generate_wifi_connection
from config_utils import pull_str_from_config
import ulogging
import time

logger = ulogging.get_logger("main")

class BeepBeep:
    def __init__(
            self,
            network_config: Path = Path("configuration/network.json"),
            hardware_config: Path = Path("configuration/hardware.json"),
            general_config: Path = Path("configuration/general.json"),
    ):
        self.general_config = json.loads(general_config.read_text())
        self.hardware_config = json.loads(hardware_config.read_text())
        self.network_config = json.loads(network_config.read_text())
        self.wifi = generate_wifi_connection(config_json=json.loads(network_config.read_text()))
        self.websocket = generate_websocket(
            hardware_config_json=self.hardware_config,
            network_config_json=self.network_config,
            general_config_json=self.general_config,
        )
        self._packet_queue: typing.List[typing.Dict[str, str]] = []
        self._listening_for_packets = Event()


    async def initialize(self):
        self.init_logging()
        await self.connect_to_network()


    async def connect_to_network(self):

        wifi_task = asyncio.create_task(self.wifi.maintain_wifi_connection())
        websocket_task = asyncio.create_task(self.listen_for_packets())
        await wifi_task
        await websocket_task
        logger.info("All network coroutines have exited")

    def stop_network(self):
        logger.info("Stopping WiFi connection...")
        self.wifi.stop()
        logger.info("Stopping websocket connection...")
        self._listening_for_packets.clear()

    async def _connect_to_websocket(self, timeout: int = 60) -> bool:
        if not self._listening_for_packets.is_set():
            raise RuntimeError("You must be listening for packets before connecting to a websocket")
        for attempt in range(0, timeout):
            logger.info("Connecting to websocket...")
            if await self._connect_websocket_if_wifi():
                return True
            if not self._listening_for_packets.is_set():
                logger.info("Aborting websocket connection attempt")
                return True
            await asyncio.sleep(1)
        logger.error("Unable to connect to websocket")
        return False

    async def _connect_websocket_if_wifi(self) -> bool:
        if self.wifi.connected:
            if self.websocket.connect(local_ip=self.wifi.local_ip):
                logger.info("Connected to websocket")
                return True
            return False
        else:
            logger.info("Cannot connect to websocket, no WiFi")
            return False

    def test_websocket(self):
        if not self.websocket.connected:
            logger.error("Websocket not connected")
        card_id: str = "27"
        interlock_packet = {
            "command": "interlock_session_start",
            "card_id": card_id,
        }
        self.websocket.send_str(json.dumps(interlock_packet))

    def init_logging(self):
        log_level = pull_str_from_config(config_json=self.general_config, key="log_level", optional=True)
        if log_level is None:
            log_level = "INFO"
        log_level = log_level.upper()
        ulogging.basic_config(level=log_level)
        logger.debug("Logging initialized")

    async def listen_for_packets(self):
        self._listening_for_packets.set()
        while self._listening_for_packets.is_set():
            if self.websocket.connected:
                recv = self.websocket.recv()
                if recv:
                    logger.info(f"Got packet {recv} from MemberMatters")
                    self._packet_queue.append(json.loads(recv))
            else:
                logger.warn("Socket disconnected!")
                logger.info("Reconnecting websocket...")
                await self._connect_to_websocket()

    async def get_packet(self) -> typing.Dict[str, str]:
        return self._packet_queue.pop(0)

    @property
    def has_packet(self) -> bool:
        return bool(self._packet_queue)