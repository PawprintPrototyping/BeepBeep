from networking import WIFI, WEBSOCKET
from config_utils import pull_str_from_config
from pathlib import Path
import json
import ulogging

logger = ulogging.get_logger("main")

def init_logging():
    log_level = pull_str_from_config(config_json=json.loads(Path("configuration/general.json").read_text()), key="log_level", optional=True)
    if log_level is None:
        log_level = "INFO"
    log_level = log_level.upper()
    ulogging.basic_config(level=log_level)

def connect_to_network():
    logger.info("Connecting to wifi...")
    WIFI.connect_wifi()
    if WIFI.connected:
        logger.info(f"Connected to {WIFI.ssid}")
    else:
        logger.error(f"Unable to connect to {WIFI.ssid}")
    logger.info("Connecting to websocket...")
    WEBSOCKET.connect(local_ip=WIFI.local_ip)
    logger.debug(f"{WEBSOCKET.recv()}")
    logger.info("Connected to websocket")

def test_websocket():
    if not WEBSOCKET.connected:
        logger.error("Websocket not connected")
    interlock_packet = {
           "command": "interlock_session_start",
            "card_id": "0xdeadbeef",
        }
    WEBSOCKET.send_str(json.dumps(interlock_packet))
    interlock_packet = {
        "command": "interlock_session_end",
        "session_id": 0,
        "session_kwh": 1,
        "card_id": 0xdeadbeef,
    }
    WEBSOCKET.send_str(json.dumps(interlock_packet))

def main():
    init_logging()
    connect_to_network()
    test_websocket()

main()