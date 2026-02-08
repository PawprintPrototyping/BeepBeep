from .hardware import Hardware
from .hardware_config import generate_hardware
from .buzzer import Buzzer
from .lock import Lock
from .status_led import StatusLed

from pathlib import Path
import json

# TODO: Real config file here
HARDWARE = generate_hardware(config_json=json.loads(Path("hardware_config.json").read_text()))

__all__ = [
    "HARDWARE",
    "Buzzer",
    "Lock",
    "StatusLed"
]
