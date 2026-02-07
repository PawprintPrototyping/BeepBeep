import typing
from abc import ABC, abstractmethod
from enum import Enum
from machine import Pin
import time

class LockTypes(Enum):
    sensible_lock = "sensible_lock"
    simple_lock = "simple_lock"

class Lock(ABC):
    def __init__(self, lock_pin: Pin, pin_reversed: bool):
        self._lock_pin: Pin = lock_pin
        self._pin_reversed: bool = pin_reversed
        # initialize the lock state
        self.lock()

    def unlock(self) -> bool:
        if self._pin_reversed:
            self._lock_pin.off()
        else:
            self._lock_pin.on()
        return True

    def lock(self) -> bool:
        if self._pin_reversed:
            self._lock_pin.on()
        else:
            self._lock_pin.off()
        return True

    def is_locked(self) -> bool:
        """True if locked, false if unlocked"""
        if self._pin_reversed:
            return not bool(self._lock_pin.value())
        else:
            return bool(self._lock_pin.value())


class SimpleLock(Lock):
    ...

class SensibleLock(Lock):
    def __init__(self, lock_pin: Pin, pin_reversed: bool, sense_pin: Pin, sense_pin_reversed: bool, wait_for_sensor_time: typing.Optional[int] = 5):
        super().__init__(lock_pin=lock_pin, pin_reversed=pin_reversed)
        self._sense_pin: Pin = sense_pin
        if sense_pin_reversed is None:
            self._door_sense_pin_reversed: bool = False
        self._wait_for_sensor_time = wait_for_sensor_time
        self._sense_pin_reversed = sense_pin_reversed

    def is_locked(self) -> bool:
        """True is open or unlocked, false is closed or locked"""
        if self._sense_pin_reversed:
            return bool(self._sense_pin.value())
        return not bool(self._sense_pin.value())

    def unlock(self) -> bool:
        if self._pin_reversed:
            self._lock_pin.off()
        else:
            self._lock_pin.on()
        for attempts in range(0, self._wait_for_sensor_time * 3):
            if not self.is_locked():
                return True
            time.sleep(.33)
        return False

    def lock(self) -> bool:
        if self._pin_reversed:
            self._lock_pin.on()
        else:
            self._lock_pin.off()
        for attempts in range(0, self._wait_for_sensor_time * 3):
            if self.is_locked():
                return True
            time.sleep(.33)
        return False
