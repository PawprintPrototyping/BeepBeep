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
    logger.info(f"Connected? {WIFI.connected}")
    WEBSOCKET.connect()

def main():
    init_logging()
    connect_to_network()

main()