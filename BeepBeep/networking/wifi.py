import network
import ubinascii
import time
import ulogging
import asyncio

logger = ulogging.get_logger("wifi")

class WifiConnection:
    def __init__(self, ssid: str, password: str, chosen_hostname: str = ""):
        self.sta_if = network.WLAN(network.STA_IF)
        self.local_ip = None
        self.local_mac = ubinascii.hexlify(self.sta_if.config("mac")).decode()  # store our mac address
        if not chosen_hostname:
            chosen_hostname = "BeepBeep_" + self.local_mac
        network.hostname(chosen_hostname)
        network.country("US")
        self._ssid = ssid
        self._password = password
        self._maintaining_wifi_connection = asyncio.Event()

    async def maintain_wifi_connection(self):
        self._maintaining_wifi_connection.set()
        while self._maintaining_wifi_connection.is_set():
            if not self.connected:
                logger.info("WiFi is not connected. Connecting...")
                if not await self.connect_wifi():
                    logger.error(f"Unable to connect to WiFi access point {self.ssid}")
            await asyncio.sleep(1)

    async def stop(self):
        self._maintaining_wifi_connection.clear()

    async def connect_wifi(self, timeout: int = 30) -> bool:
        logger.debug(f"Connecting to SSID {self._ssid}, password: {'*' * len(self._password)}")
        if self.sta_if.isconnected():
            self.sta_if.disconnect()
            time.sleep(0.5)

        self.sta_if.active(False)
        time.sleep(0.5)
        self.sta_if.active(True)

        self.sta_if.connect(self._ssid, self._password)
        for attempt in range(0, timeout):
            logger.debug("Waiting for connection...")
            await asyncio.sleep(1)
            if self.connected:
                return True
            if not self._maintaining_wifi_connection.is_set():
                logger.info("Aborting connection attempt")
                return True
        return False

    @property
    def connected(self) -> bool:
        return self.sta_if.isconnected()

    @property
    def ssid(self) -> str:
        return self._ssid