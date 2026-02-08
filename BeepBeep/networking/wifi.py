import network
import ubinascii
import time
import ulogging

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

    def connect_wifi(self, timeout: int = 30) -> bool:
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
            time.sleep(1)
            if self.sta_if.isconnected():
                return True
        return False

    @property
    def connected(self) -> bool:
        return self.sta_if.isconnected()