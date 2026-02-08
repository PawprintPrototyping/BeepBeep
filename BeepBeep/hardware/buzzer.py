from machine import Pin

from enum import Enum
from abc import ABC, abstractmethod

class BuzzerTypes(Enum):
    simple = "simple"
    pwm = "pwm"

class Buzzer(ABC):
    def __init__(self, buzzer_pin: Pin):
        self._pin: Pin = buzzer_pin

    @abstractmethod
    async def on(self):
        ...

    @abstractmethod
    def off(self):
        ...


class SimpleBuzzer(Buzzer):
    """
    Basic buzzer that only requires a signal be asserted in order for it to produce a tone
    """
    def __init__(self, buzzer_pin: Pin, pin_reversed: bool):
        super().__init__(buzzer_pin=buzzer_pin)
        self._pin_reversed: bool = pin_reversed

    def on(self) -> None:
        if self._pin_reversed:
            self._pin.off()
        else:
            self._pin.on()

    def off(self) -> None:
        if self._pin_reversed:
            self._pin.on()
        else:
            self._pin.off()


class PwmBuzzer(Buzzer):
    def __init__(self, buzzer_pin: Pin):
        super().__init__(buzzer_pin=buzzer_pin)
        self._frequency_hz: int = 500

    def set_pwm_frequency(self, frequency_hz: int):
        self._frequency_hz = frequency_hz

    def on(self) -> None:
        # TODO: PWM driver
        return

    def off(self) -> None:
        # TODO: PWM driver
        return