import typing

from .. import ulogging
import time
import config

from .buzzer import Buzzer, SimpleBuzzer, PwmBuzzer, BuzzerTypes
from .status_led import SimpleStatusLed, NeopixelStatusLed
from .lock import SimpleLock, SensibleLock
from .hardware import Hardware, DeviceType
from .card_reader import CardReader, CardReaderTypes, Pn532I2c, Pn532Uart, Wiegand, Rdm6300
from BeepBeep.config_utils import pull_int_from_config, pull_bool_from_config, pull_str_from_config
from BeepBeep.hardware.ulcdscreen import LcdScreen
from machine import WDT, Pin, I2C, UART

ulogging.basic_config(level=config.LOG_LEVEL)
logger = ulogging.get_logger("hardware_config")

def handle_card_reader(config_json: typing.Dict) -> CardReader:
    if "card_reader" not in config_json:
        raise ValueError("No card reader is specified in the hardware config")
    card_reader_json = config_json["card_reader"]
    if "type" not in card_reader_json.keys():
        raise ValueError("No card reader type is specified in the card_reader hardware config")
    card_reader_type  = card_reader_json["type"]
    if card_reader_type == CardReaderTypes.Pn532I2c.value:
        sda_pin: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="sda_pin",
                                                             optional=False)
        scl_pin: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="scl_pin",
                                                             optional=False)
        card_baud: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="card_baud",
                                                               optional=True)
        read_timeout_ms: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="read_timeout_ms",
                                                                     optional=True)
        i2c_freq: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="i2c_freq",
                                                              optional=True)
        if i2c_freq is None:
            i2c_freq = 400000
        return Pn532I2c(I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=i2c_freq), card_baud=card_baud, read_timeout_ms=read_timeout_ms)
    elif card_reader_type == CardReaderTypes.Pn532Uart.value:
        tx_pin: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="tx_pin",
                                                            optional=False)
        rx_pin: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="rx_pin",
                                                            optional=False)
        card_baud: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="card_baud",
                                                               optional=True)
        read_timeout_ms: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json,
                                                                     key="read_timeout_ms",
                                                                     optional=True)
        return Pn532Uart(UART(0, rx=Pin(rx_pin), tx=Pin(tx_pin), baudrate=115200), card_baud=card_baud,
                        read_timeout_ms=read_timeout_ms)
    elif card_reader_type == CardReaderTypes.Rdm6300.value:
        tx_pin: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="tx_pin",
                                                            optional=False)
        rx_pin: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="rx_pin",
                                                            optional=False)
        return Rdm6300(UART(0, rx=Pin(rx_pin), tx=Pin(tx_pin), baudrate=9600))
    elif card_reader_type == CardReaderTypes.Wiegand.value:
        pin0: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="pin0",
                                                          optional=False)
        pin1: typing.Optional[int] = pull_int_from_config(config_json=card_reader_json, key="pin1",
                                                          optional=False)
        uid_32bit_mode: typing.Optional[bool] = pull_bool_from_config(config_json=card_reader_json, key="uid_32but_mode",
                                                                      optional=True)
        if uid_32bit_mode is None:
            uid_32bit_mode = False
        return Wiegand(pin0=Pin(pin0), pin1=Pin(pin1), uid_32bit_mode=uid_32bit_mode)
    raise ValueError(f"Invalid card reader type in card_reader hardware config. Supported card reader types: {', '.join([reader_type.value for reader_type in CardReaderTypes])}")

def _handle_wdt(config_json: typing.Dict) -> typing.Optional[WDT]:
    wdt: typing.Optional[WDT] = None
    enable_wdt: bool = pull_bool_from_config(config_json=config_json, key="enable_wdt", optional=True)
    if enable_wdt:
        fixed_unlock_delay: int = pull_int_from_config(config_json=config_json, key="fixed_unlock_delay", optional=True)
        if fixed_unlock_delay is None:
            fixed_unlock_delay = 2
        logger.warn("Press CTRL+C to stop the WDT starting...")
        time.sleep(3)
        wdt = WDT(timeout=fixed_unlock_delay * 2000 + 5000)
    return wdt

def _handle_lcd(config_json: typing.Dict) -> typing.Optional[LcdScreen]:
    i2c: typing.Optional[I2C] = None
    lcd: typing.Optional[LcdScreen] = None
    if "lcd" not in config_json.keys():
        return lcd
    lcd_config = config_json["lcd"]
    sda_pin: typing.Optional[int] = pull_int_from_config(config_json=lcd_config, key="sda_pin",
                                                         optional=True)
    scl_pin: typing.Optional[int] = pull_int_from_config(config_json=lcd_config, key="scl_pin",
                                                         optional=True)

    i2c_frequency: typing.Optional[int] = pull_int_from_config(config_json=lcd_config, key="i2c_freq",
                                                               optional=True)
    if i2c_frequency is None:
        i2c_frequency = 400000

    if sda_pin is not None and scl_pin is not None:
        i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=i2c_frequency)

    # Handle the screen or lack thereof
    lcd_address = pull_int_from_config(config_json=lcd_config, key="lcd_address", optional=True)
    if lcd_address is not None:
        if i2c is None:
            raise ValueError("I2C address is given for an LCD screen, but no pins are given for I2C in the hardware "
                             "config")
        lcd_cols = pull_int_from_config(config_json=lcd_config, key="lcd_cols", optional=True)
        lcd_rows = pull_int_from_config(config_json=lcd_config, key="lcd_rows", optional=True)
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
    return lcd

def _handle_buzzer(config_json: typing.Dict) -> typing.Optional[Buzzer]:
    buzzer: typing.Optional[Buzzer] = None
    buzzer_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="buzzer_pin",
                                                            optional=True)
    if buzzer_pin is not None:
        buzzer_type: typing.Optional[str] = pull_str_from_config(config_json=config_json, key="buzzer_type",
                                                                 optional=True)
        if buzzer_type is None:
            buzzer_type = BuzzerTypes.simple.value
        if buzzer_type not in [all_buzzers.value for all_buzzers in BuzzerTypes]:
            raise ValueError(
                f"Invalid buzzer type {buzzer_type} set in the hardware config. Valid buzzer types are {', '.join([all_buzzers.value for all_buzzers in BuzzerTypes])}")
        if buzzer_type == BuzzerTypes.simple.value:
            buzzer_reversed = pull_bool_from_config(config_json=config_json, key="buzzer_reversed", optional=True)
            if buzzer_reversed is None:
                buzzer_reversed = False
            buzzer = SimpleBuzzer(buzzer_pin=Pin(buzzer_pin, Pin.OUT), pin_reversed=buzzer_reversed)
        elif buzzer_type == BuzzerTypes.pwm.value:
            buzzer = PwmBuzzer(buzzer_pin=Pin(buzzer_pin, Pin.OUT))
    return buzzer

def _handle_rgb_status_led(config_json: typing.Dict) -> typing.Optional[NeopixelStatusLed]:
    rgb_status_led: typing.Optional[NeopixelStatusLed] = None
    rgb_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="rgb_led_pin", optional=True)
    if rgb_pin is not None:
        num_neopixels = pull_int_from_config(config_json=config_json, key="num_rgb_led", optional=True)
        if num_neopixels is None:
            num_neopixels = 1
        rgb_status_led = NeopixelStatusLed(led_pin=Pin(rgb_pin, Pin.OUT), num_neopixels=num_neopixels)
    return rgb_status_led

def _handle_reader_led(config_json: typing.Dict) -> typing.Optional[SimpleStatusLed]:
    reader_status_led: typing.Optional[SimpleStatusLed] = None
    reader_led_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="reader_led_pin",
                                                                optional=True)
    if reader_led_pin is not None:
        reader_led_reversed: bool = pull_bool_from_config(config_json=config_json, key="reader_led_reversed",
                                                          optional=True)
        if reader_led_reversed is None:
            reader_led_reversed = False
        reader_status_led = SimpleStatusLed(led_pin=Pin(reader_led_pin, Pin.OUT), pin_reversed=reader_led_reversed)
    return reader_status_led

def _handle_door_lock(config_json: typing.Dict) -> typing.Optional[typing.Union[SimpleLock, SensibleLock]]:
    door: typing.Optional[typing.Union[SimpleLock, SensibleLock]] = None
    door_lock_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="door_lock_pin",
                                                               optional=True)
    if door_lock_pin is not None:
        door_sensor_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json,
                                                                     key="door_sensor_pin", optional=True)
        door_lock_reversed: bool = pull_bool_from_config(config_json=config_json, key="door_lock_reversed",
                                                         optional=True)
        if door_lock_reversed is None:
            door_lock_reversed = False
        if door_sensor_pin is not None:
            door_sensor_reversed: bool = pull_bool_from_config(config_json=config_json,
                                                               key="door_sensor_reversed",
                                                               optional=True)
            if door_sensor_reversed is None:
                door_lock_reversed = False
            door = SensibleLock(lock_pin=Pin(door_lock_pin, Pin.OUT), pin_reversed=door_lock_reversed,
                                sense_pin=Pin(door_sensor_pin, Pin.IN), sense_pin_reversed=door_sensor_reversed)
        else:
            door = SimpleLock(lock_pin=Pin(door_lock_pin, Pin.OUT), pin_reversed=door_lock_reversed)
    return door

def _handle_relay(config_json: typing.Dict) -> typing.Optional[SimpleLock]:
    relay: typing.Optional[SimpleLock] = None
    relay_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="relay_pin", optional=True)
    if relay_pin is not None:
        relay_reversed: bool = pull_bool_from_config(config_json=config_json, key="relay_reversed",
                                                     optional=True)
        if relay_reversed is None:
            relay_reversed = False
        relay = SimpleLock(lock_pin=Pin(relay_pin, Pin.OUT), pin_reversed=relay_reversed)
    return relay


def generate_hardware(config_json: typing.Dict) -> Hardware:
    device_type_str = pull_str_from_config(config_json=config_json, key="device_type", optional=False).rstrip()
    try:
        device_type: DeviceType = DeviceType(device_type_str)
    except ValueError:
        raise ValueError(f"{device_type_str} is not a valid device_type. Valid device_types are {', '.join([all_device_types.value for all_device_types in DeviceType])}")
    in_1_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="in_1_pin",
                                                          optional=True)
    out_1_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="out_1_pin",
                                                           optional=True)
    aux_1_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="aux_1_pin",
                                                           optional=True)
    aux_2_pin: typing.Optional[int] = pull_int_from_config(config_json=config_json, key="aux_2_pin",
                                                           optional=True)
    wdt = _handle_wdt(config_json=config_json)
    lcd = _handle_lcd(config_json=config_json)
    buzzer = _handle_buzzer(config_json=config_json)
    rgb_status_led = _handle_rgb_status_led(config_json=config_json)
    reader_status_led = _handle_reader_led(config_json=config_json)
    door = _handle_door_lock(config_json=config_json)
    relay = _handle_relay(config_json=config_json)
    card_reader = handle_card_reader(config_json=config_json)

    return Hardware(
        buzzer=buzzer, rgb_status_led=rgb_status_led, reader_status_led=reader_status_led, lcd=lcd, wdt=wdt,
        in_1_pin=in_1_pin, out_1_pin=out_1_pin, aux_1_pin=aux_1_pin, aux_2_pin=aux_2_pin, door=door, relay=relay,
        card_reader=card_reader, device_type=device_type
    )
