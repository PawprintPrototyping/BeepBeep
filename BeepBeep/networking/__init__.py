from networking.networking_config import generate_wifi_connection
import json
from pathlib import Path

WIFI = generate_wifi_connection(config_json=json.loads(Path("configuration/network_config.json").read_text()))

__all__ = [
    "WIFI"
]