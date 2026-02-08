from enum import Enum
import time
from abc import ABC, abstractmethod
from neopixel import NeoPixel

import typing
from machine import Pin

class StatusLedTypes(Enum):
    simple = "simple"
    neopixel = "neopixel"

# WS2812 uses GRB instead of RGB!
RGB_OFF = (0, 0, 0)
RGB_WHITE = (255, 255, 255)
RGB_RED = (0, 255, 0)
RGB_GREEN = (255, 0, 0)
RGB_BLUE = (0, 0, 255)
RGB_YELLOW = (255, 255, 0)
RGB_PURPLE = (0, 130, 130)
RGB_PINK = (0, 200, 50)

# Easy names for common colors
STANDBY_COLOR = RGB_BLUE
UNLOCKED_COLOR = RGB_GREEN

class StatusLed(ABC):

    def __init__(self, led_pin: Pin):
        self._pin: Pin = led_pin

    @abstractmethod
    def led_on(self):
        ...

    @abstractmethod
    def led_off(self):
        ...

    @abstractmethod
    def led_happy(self):
        ...

    @abstractmethod
    def led_neutral(self):
        ...

    @abstractmethod
    def led_sad(self):
        ...

    @abstractmethod
    def led_error(self):
        ...


class SimpleStatusLed(StatusLed):
    def __init__(self, led_pin: Pin, pin_reversed: bool):
        super().__init__(led_pin=led_pin)
        self._pin_reversed: bool = pin_reversed

    def led_on(self):
        if self._pin_reversed:
            self._pin.off()
        else:
            self._pin.on()

    def led_off(self):
        if self._pin_reversed:
            self._pin.on()
        else:
            self._pin.off()

    def led_happy(self):
        self.led_on()

    def led_sad(self):
        self.led_on()

    def led_error(self):
        self.led_on()

    def led_neutral(self):
        self.led_on()


class NeopixelStatusLed(StatusLed):
    def __init__(self,
                 led_pin: Pin,
                 num_neopixels: int,
                 happy_color: typing.Tuple[int, int, int] = RGB_GREEN,
                 neutral_color: typing.Tuple[int, int, int] = RGB_BLUE,
                 sad_color: typing.Tuple[int, int, int] = RGB_RED,
                 error_color: typing.Tuple[int, int, int] = RGB_YELLOW
                 ):
        super().__init__(led_pin=led_pin)
        self._current_color: typing.Tuple[int, int, int] = RGB_WHITE
        self._num_neopixels = num_neopixels
        self._neopixel = NeoPixel(
            self._pin, n=self._num_neopixels
        )
        self._happy_color: typing.Tuple[int, int, int] = happy_color
        self._neutral_color: typing.Tuple[int, int, int] = neutral_color
        self._sad_color: typing.Tuple[int, int, int] = sad_color
        self._error_color: typing.Tuple[int, int, int] = error_color

    def led_on(self):
        for neopixel in range(0, self._num_neopixels):
            self._neopixel[neopixel] = self._current_color
            self._neopixel.write()

    def led_off(self):
        for neopixel in range(0, self._num_neopixels):
            self._neopixel[neopixel] = RGB_OFF
        self._neopixel.write()

    def set_color(self, color: typing.Tuple[int, int, int]):
        self._current_color = color

    def led_happy(self):
        self.set_color(color=self._happy_color)
        self.led_on()

    def led_sad(self):
        self.set_color(color=self._sad_color)
        self.led_on()

    def led_neutral(self):
        self.set_color(color=self._neutral_color)
        self.led_on()

    def led_error(self):
        self.set_color(color=self._error_color)
        self.led_on()

    def colorwheel(self) -> None:
        pos = ((time.ticks_ms() / 1000) * 100) % 255
        if pos < 0 or pos > 255:
            self.set_color(color=(0, 0, 0))
            self.led_on()
        if pos < 85:
            self.set_color((int(255 - pos * 3), int(pos * 3), 0))
            self.led_on()
        if pos < 170:
            pos -= 85
            self.set_color((0, int(255 - pos * 3), int(pos * 3)))
            self.led_on()
        pos -= 170
        self.set_color((int(pos * 3), 0, int(255 - pos * 3)))
        self.led_on()