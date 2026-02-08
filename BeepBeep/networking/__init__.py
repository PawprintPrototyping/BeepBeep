from networking.networking_config import generate_wifi_connection, generate_websocket
import json
from pathlib import Path

WIFI = generate_wifi_connection(config_json=json.loads(Path("configuration/network.json").read_text()))
WEBSOCKET = generate_websocket(
    hardware_config_json=json.loads(Path("configuration/hardware.json").read_text()),
    network_config_json=json.loads(Path("configuration/network.json").read_text()),
    general_config_json=json.loads(Path("configuration/general.json").read_text())
)

__all__ = [
    "WIFI",
    "WEBSOCKET",
]