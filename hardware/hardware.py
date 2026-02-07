import typing
import config
import time
import ulogging
from networking import urequests

from enum import Enum

from machine import WDT, Pin
from ulcdscreen import LcdScreen

from .buzzer import Buzzer
from .status_led import SimpleStatusLed, NeopixelStatusLed
from .lock import Lock, SimpleLock

ulogging.basicConfig(level=config.LOG_LEVEL)
logger = ulogging.getLogger("hardware")


class DeviceType(Enum):
    door = "door"
    interlock = "interlock"
    vend = "vend"


class Hardware:

    # TODO: Creds in an HTTP get request are a very bad idea
    # TODO: Put this Tasmota stuff elsewhere, it's not hardware
    TASMOTA_BASE_URL = f"http://{config.TASMOTA_HOST}/cm?user={config.TASMOTA_USER}&password={config.TASMOTA_PASSWORD}&cmnd="

    def __init__(
            self,
            buzzer: typing.Optional[Buzzer],
            rgb_status_led: typing.Optional[NeopixelStatusLed],
            reader_status_led: typing.Optional[SimpleStatusLed],
            lcd: typing.Optional[LcdScreen],
            wdt: typing.Optional[WDT],
            in_1_pin: typing.Optional[Pin],
            out_1_pin: typing.Optional[Pin],
            aux_1_pin: typing.Optional[Pin],
            aux_2_pin: typing.Optional[Pin],
            door: typing.Optional[Lock],
            relay: typing.Optional[SimpleLock]
    ):
        self.buzzer: typing.Optional[Buzzer] = buzzer
        self.rgb_status_led: typing.Optional[NeopixelStatusLed] = rgb_status_led
        self.reader_status_led: typing.Optional[SimpleStatusLed] = reader_status_led
        self.lcd: typing.Optional[LcdScreen] = lcd
        self.wdt: typing.Optional[WDT] = wdt
        self.in_1_pin: typing.Optional[Pin] = in_1_pin
        self.out_1_pin: typing.Optional[Pin] = out_1_pin
        self.aux_1_pin: typing.Optional[Pin] = aux_1_pin
        self.aux_2_pin: typing.Optional[Pin] = aux_2_pin
        self.door: typing.Optional[Lock] = door
        self.relay: typing.Optional[SimpleLock] = relay


    @property
    def buzzer_enabled(self) -> bool:
        return self.buzzer is not None

    @property
    def rgb_status_led_enabled(self) -> bool:
        return self.rgb_status_led is not None

    @property
    def reader_status_led_enabled(self) -> bool:
        return self.reader_status_led is not None

    @property
    def wdt_enabled(self) -> bool:
        return self.wdt is not None

    @property
    def lcd_enabled(self) -> bool:
        return self.lcd is not None

    @property
    def relay_enabled(self) -> bool:
        return self.relay is not None

    @property
    def door_enabled(self) -> bool:
        return self.door is not None

    def feed_wdt(self) -> None:
        if self.wdt_enabled:
            self.wdt.feed()

    def alert(self) -> None:
        self.buzzer.on() if self.buzzer_enabled else ...
        self.reader_status_led.led_on() if self.reader_status_led_enabled else ...
        self.rgb_status_led.led_sad() if self.rgb_status_led_enabled else ...
        time.sleep(0.3)

        self.buzzer.off() if self.buzzer_enabled else ...
        self.reader_status_led.led_off() if self.reader_status_led_enabled else ...
        self.rgb_status_led.led_off() if self.rgb_status_led_enabled else ...
        time.sleep(0.3)

        self.buzzer.on() if self.buzzer_enabled else ...
        self.reader_status_led.led_on() if self.reader_status_led_enabled else ...
        self.rgb_status_led.led_sad() if self.rgb_status_led_enabled else ...
        time.sleep(0.3)

        self.buzzer.off() if self.buzzer_enabled else ...
        self.reader_status_led.led_off() if self.reader_status_led_enabled else ...
        self.rgb_status_led.led_off() if self.rgb_status_led_enabled else ...
        time.sleep(0.3)

    def buzz_ok(self) -> None:
        self.buzzer.on() if self.buzzer_enabled else ...
        self.reader_status_led.led_on() if self.reader_status_led_enabled else ...
        self.rgb_status_led.led_happy() if self.rgb_status_led_enabled else ...

        time.sleep(1)

        self.buzzer.off() if self.buzzer_enabled else ...
        self.reader_status_led.led_off() if self.reader_status_led_enabled else ...
        self.rgb_status_led.led_neutral() if self.rgb_status_led_enabled else ...

    def buzz_card_read(self) -> None:
        self.buzzer.on() if self.buzzer_enabled else ...
        time.sleep(0.2)
        self.buzzer.off() if self.buzzer_enabled else ...

    def buzz_action(self) -> None:
        self.buzzer.on() if self.buzzer_enabled else ...
        time.sleep(config.ACTION_BUZZ_DELAY)

    def interlock_session_started(self) -> None:
        self.rgb_status_led.led_happy() if self.rgb_status_led_enabled else ...
        self.reader_status_led.led_on() if self.reader_status_led_enabled else ...
        self.buzz_action()

    def interlock_session_ended(self) -> None:
        self.rgb_status_led.led_neutral() if self.rgb_status_led_enabled else ...
        self.reader_status_led.led_off() if self.reader_status_led_enabled else ...

    @classmethod
    def reset_interlock_power_usage(cls) -> bool:
        if config.TASMOTA_HOST:
            logger.debug("Resetting power usage from remote interlock!")
            r = urequests.get(
                Hardware.TASMOTA_BASE_URL + "Backlog%20EnergyToday%200%3B%20EnergyTotal%200%3B"
            )
            return True
        return False


    def interlock_power_control(self, status: bool) -> None:
        if status:
            if config.TASMOTA_HOST:
                logger.info("Trying to turn ON remote interlock!")
                urequests.get(Hardware.TASMOTA_BASE_URL + f"Power%20On")

            else:
                self.relay.unlock() if self.relay_enabled else ...
        else:
            if config.TASMOTA_HOST:
                logger.info("Trying to turn OFF remote interlock!")
                urequests.get(Hardware.TASMOTA_BASE_URL + f"Power%20Off")
            else:
                self.relay.lock() if self.relay_enabled else ...

    @classmethod
    def get_interlock_power_usage(cls) -> typing.Optional[float]:
        if config.TASMOTA_HOST:
            logger.debug("Getting power usage from remote interlock!")
            r = urequests.get(Hardware.TASMOTA_BASE_URL + "EnergyTotal")
            return float(r.json()["EnergyTotal"]["Total"])
        else:
            return None

    # TODO: Deal with these pins
    # def out_1_on():
    #     if config.OUT_1_REVERSED:
    #         out_1_pin.off()
    #     else:
    #         out_1_pin.on()


    # def out_1_off():
    #     if config.RELAY_REVERSED:
    #         relay_pin.on()
    #     else:
    #         relay_pin.off()



    def get_in_1_state(self):
        # TODO
        ...
    #     if config.IN_1_REVERSED:
    #         return not in_1_pin.value()
    #     else:
    #         return in_1_pin.value()


    # def get_aux_1_state():
    #     if config.AUX_1_REVERSED:
    #         return not aux_1_pin.value()
    #     else:
    #         return aux_1_pin.value()


    # def get_aux_2_state():
    #     if config.AUX_2_REVERSED:
    #         return not aux_2_pin.value()
    #     else:
    #         return aux_2_pin.value()

    def vend_product(self) -> None:
        # TODO: This is probably wrong, check it later
        # TODO: Also maybe assert that the relay and lock actually exist before allowing this to run
        self.rgb_status_led.led_happy() if self.rgb_status_led_enabled else ...
        self.reader_status_led.led_on() if self.reader_status_led_enabled else ...
        if config.BUZZ_ON_SWIPE:
            self.buzz_action()
        if config.VEND_MODE == "toggle":
            self.relay.unlock() if self.relay_enabled else ...
            self.door.unlock() if self.door_enabled else ...
            start_time = time.time()
            while time.time() - start_time < config.VEND_TOGGLE_TIME:
                time.sleep(0.1)
                self.feed_wdt() if self.wdt_enabled else ...
            self.relay.lock() if self.relay_enabled else ...
            self.door.lock() if self.door_enabled else ...
        elif config.VEND_MODE == "hold":
            self.relay.unlock() if self.relay_enabled else ...
            self.door.unlock() if self.door_enabled else ...
            time.sleep(1)

            while self.get_in_1_state():
                time.sleep(0.1)
            self.relay.lock() if self.relay_enabled else ...
            self.door.lock() if self.door_enabled else ...
