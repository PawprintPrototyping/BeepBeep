import typing
import ulogging
import time
import config

from .buzzer import Buzzer, SimpleBuzzer, PwmBuzzer, BuzzerTypes
from .status_led import SimpleStatusLed, NeopixelStatusLed
from .lock import SimpleLock, SensibleLock
from .hardware import Hardware, DeviceType
from ulcdscreen import LcdScreen
from machine import WDT, Pin, I2C

ulogging.basicConfig(level=config.LOG_LEVEL)
logger = ulogging.getLogger("hardware_config")

TRUTHY_STRINGS = ("yes", "y", "1", "make it so", "true", "ye")

def _pull_str_from_config(config_json: typing.Dict[str, str], key: str, optional: bool = True) -> typing.Optional[str]:
    config_value = config_json.get(key)
    if not optional and config_value is None:
        raise ValueError(f"{key} is not set in the hardware config")
    return config_value

def _pull_int_from_config(config_json: typing.Dict[str, str], key: str, optional: bool = True) -> typing.Optional[int]:
    try:
        possible_int = _pull_str_from_config(config_json=config_json, key=key, optional=optional)
        if "0x" in possible_int:
            return int(possible_int, 16)
        return int(possible_int)
    except ValueError:
        raise ValueError(f"Unable to convert {_pull_str_from_config(config_json=config_json, key=key)} to int "
                         f"while reading {key} from hardware config")

def _pull_bool_from_config(config_json: typing.Dict[str, str], key: str, optional: bool = True) -> typing.Optional[bool]:
    return _pull_str_from_config(config_json=config_json, key=key, optional=optional).replace(" ", "").rstrip().casefold() in TRUTHY_STRINGS

def generate_hardware(config_json: typing.Dict) -> Hardware:
    buzzer: typing.Optional[Buzzer] = None
    rgb_status_led: typing.Optional[NeopixelStatusLed] = None
    reader_status_led: typing.Optional[SimpleStatusLed] = None
    relay: typing.Optional[SimpleLock] = None
    door: typing.Optional[typing.Union[SimpleLock, SensibleLock]] = None
    lcd: typing.Optional[LcdScreen] = None
    wdt: typing.Optional[WDT] = None
    device_type_str = _pull_str_from_config(config_json=config_json, key="device_type", optional=False).rstrip()
    try:
        device_type: DeviceType = DeviceType(device_type_str)
    except ValueError:
        raise ValueError(f"{device_type_str} is not a valid device_type. Valid device_types are {', '.join([all_device_types.value for all_device_types in DeviceType])}")
    i2c: typing.Optional[I2C] = None
    in_1_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="in_1_pin",
                                                                optional=True)
    out_1_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="out_1_pin",
                                                                 optional=True)
    aux_1_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="aux_1_pin",
                                                                 optional=True)
    aux_2_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="aux_2_pin",
                                                                      optional=True)

    # Handle the WDT
    enable_wdt: bool = _pull_bool_from_config(config_json=config_json, key="enable_wdt", optional=True)
    if enable_wdt:
        fixed_unlock_delay: int = _pull_int_from_config(config_json=config_json, key="fixed_unlock_delay", optional=True)
        if fixed_unlock_delay is None:
            fixed_unlock_delay = 2
        logger.warn("Press CTRL+C to stop the WDT starting...")
        time.sleep(3)
        wdt = WDT(timeout=fixed_unlock_delay * 2000 + 5000)

    # Handle I2C
    sda_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="sda_pin",
                                                               optional=True)
    scl_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="scl_pin",
                                                               optional=True)

    i2c_frequency: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="i2c_freq",
                                                                     optional=True)
    if i2c_frequency is None:
        i2c_frequency = 400000

    if sda_pin is not None and scl_pin is not None:
        i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=i2c_frequency)

    # Handle the screen or lack thereof
    lcd_address = _pull_int_from_config(config_json=config_json, key="lcd_address", optional=True)
    if lcd_address is not None:
        lcd_cols = _pull_int_from_config(config_json=config_json, key="lcd_cols", optional=True)
        lcd_rows = _pull_int_from_config(config_json=config_json, key="lcd_rows", optional=True)
        i2c_devices = []
        for device in i2c.scan():
            i2c_devices.append(device)
            logger.debug(
                f"Found i2c device. Decimal address: {device} | Hexa address: {hex(device)}"
            )
        if lcd_address in i2c_devices:
            lcd = LcdScreen(
                i2c,
                i2c_address=lcd_address,
                columns=lcd_cols if lcd_cols is not None else 128,
                rows=lcd_rows if lcd_rows is not None else 64
            )
        else:
            raise RuntimeError(f"Cannot find LCD with address 0x{lcd_address:x} on the I2C bus")

    # Handle the buzzer initialization
    buzzer_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="buzzer_pin",
                                                                  optional=True)
    if buzzer_pin is not None:
        buzzer_type: typing.Optional[str] = _pull_str_from_config(config_json=config_json, key="buzzer_type", optional=True)
        if buzzer_type is None:
            buzzer_type = BuzzerTypes.simple.value
        if buzzer_type not in [all_buzzers.value for all_buzzers in BuzzerTypes]:
            raise ValueError(f"Invalid buzzer type {buzzer_type} set in the hardware config. Valid buzzer types are {', '.join([all_buzzers.value for all_buzzers in BuzzerTypes])}")
        if buzzer_type == BuzzerTypes.simple.value:
            buzzer_reversed = _pull_bool_from_config(config_json=config_json, key="buzzer_reversed", optional=True)
            if buzzer_reversed is None:
                buzzer_reversed = False
            buzzer = SimpleBuzzer(buzzer_pin=Pin(buzzer_pin, Pin.OUT), pin_reversed=buzzer_reversed)
        elif buzzer_type == BuzzerTypes.pwm.value:
            buzzer = PwmBuzzer(buzzer_pin=Pin(buzzer_pin, Pin.OUT))

    # Handle the Neopixel Status LED Initialization
    rgb_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="rgb_led_pin", optional=True)
    if rgb_pin is not None:
        num_neopixels = _pull_int_from_config(config_json=config_json, key="num_rgb_led", optional=True)
        if num_neopixels is None:
            num_neopixels = 1
        rgb_status_led = NeopixelStatusLed(led_pin=Pin(rgb_pin, Pin.OUT), num_neopixels=num_neopixels)

    # Handle reader status LED initialization
    reader_led_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="reader_led_pin", optional=True)
    if reader_led_pin is not None:
        reader_led_reversed: bool = _pull_bool_from_config(config_json=config_json, key="reader_led_reversed", optional=True)
        if reader_led_reversed is None:
            reader_led_reversed = False
        reader_status_led = SimpleStatusLed(led_pin=Pin(reader_led_pin, Pin.OUT), pin_reversed=reader_led_reversed)

    # Handle the door lock
    door_lock_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="door_lock_pin", optional=True)
    if door_lock_pin is not None:
        door_sensor_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json,
                                                                           key="door_sensor_pin", optional=True)
        door_lock_reversed: bool = _pull_bool_from_config(config_json=config_json, key="door_lock_reversed",
                                                               optional=True)
        if door_lock_reversed is None:
            door_lock_reversed = False
        if door_sensor_pin is not None:
            door_sensor_reversed: bool = _pull_bool_from_config(config_json=config_json,
                                                                     key="door_sensor_reversed",
                                                                     optional=True)
            if door_sensor_reversed is None:
                door_lock_reversed = False
            door = SensibleLock(lock_pin=Pin(door_lock_pin, Pin.OUT), pin_reversed=door_lock_reversed, sense_pin=Pin(door_sensor_pin, Pin.IN), sense_pin_reversed=door_sensor_reversed)
        else:
            door = SimpleLock(lock_pin=Pin(door_lock_pin, Pin.OUT), pin_reversed=door_lock_reversed)

    # Handle the relay pin
    relay_pin: typing.Optional[int] = _pull_int_from_config(config_json=config_json, key="relay_pin", optional=True)
    if relay_pin is not None:
        relay_reversed: bool = _pull_bool_from_config(config_json=config_json, key="relay_reversed",
                                                           optional=True)
        if relay_reversed is None:
            relay_reversed = False
        relay = SimpleLock(lock_pin=Pin(relay_pin, Pin.OUT), pin_reversed=relay_reversed)

    return Hardware(
        buzzer=buzzer, rgb_status_led=rgb_status_led, reader_status_led=reader_status_led, lcd=lcd, wdt=wdt,
        in_1_pin=in_1_pin, out_1_pin=out_1_pin, aux_1_pin=aux_1_pin, aux_2_pin=aux_2_pin, door=door, relay=relay
    )
