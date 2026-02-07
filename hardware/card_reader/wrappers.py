from abc import ABC, abstractmethod
from urdm6300 import Rdm6300
from uwiegand import Wiegand
from pn532.i2c import PN532_I2C
from pn532.uart import PN532_UART
from pn532.pn532 import _MIFARE_ISO14443A as MIFARE_ISO14443A  # yeah yeah private variable, be quiet
from machine import UART, Pin, I2C
import typing
from enum import Enum

class CardReaderTypes(Enum):
    Rdm6300 = "rdm6300"
    Wiegand = "wiegand"
    Pn532I2c = "pn532i2c"
    Pn532Uart = "pn532uart"

class CardReaderWrapper(ABC):
    def __init__(self):
        self._card_reader_obj = None

    @abstractmethod
    def read_card(self) -> bytes:
        """
        Read a card. This should return bytes, in little endian (where applicable), to maximize compatibility with as
        many card reader types as possible
        """
        ...


class WrappedRdm6300(CardReaderWrapper):
    def __init__(self, uart: UART):
        super().__init__()
        self._card_reader_obj: Rdm6300 = Rdm6300(
            uart=uart
        )

    def read_card(self) -> bytes:
        return self._card_reader_obj.read_card().encode('utf-8')


class WrappedWiegand(CardReaderWrapper):
    def __init__(self, pin0: Pin, pin1: Pin, callback = None, timer_id: int = -1, uid_32bit_mode: bool = False):
        super().__init__()
        self._card_reader_obj: Wiegand = Wiegand(
            pin0=pin0,
            pin1=pin1,
            callback=callback,
            timer_id=timer_id,
            uid_32bit_mode=uid_32bit_mode
        )

    def read_card(self) -> bytes:
        return self._card_reader_obj.read_card().to_bytes(byteorder="little")


class WrappedPn532I2c(CardReaderWrapper):
    def __init__(self, i2c: I2C, reset: typing.Optional[Pin] = None, card_baud: typing.Optional[int] = None, read_timeout_ms: typing.Optional[int] = None):
        super().__init__()
        self._card_reader_obj: PN532_I2C = PN532_I2C(i2c=i2c, reset=reset)
        self._card_baud: int = card_baud
        if self._card_baud is None:
            self._card_baud = MIFARE_ISO14443A
        self._read_timeout_ms: int = read_timeout_ms
        if self._read_timeout_ms is None:
            self._read_timeout_ms = 1000

    def read_card(self) -> bytes:
        return bytes(self._card_reader_obj.read_passive_target(card_baud=self._card_baud, timeout=self._read_timeout_ms))


class WrappedPn532Uart(CardReaderWrapper):
    def __init__(self, uart: UART, reset: typing.Optional[Pin] = None, card_baud: typing.Optional[int] = None, read_timeout_ms: typing.Optional[int] = None):
        super().__init__()
        self._card_reader_obj: PN532_UART = PN532_UART(uart=uart, reset=reset)
        self._card_baud: int = card_baud
        if self._card_baud is None:
            self._card_baud = MIFARE_ISO14443A
        self._read_timeout_ms: int = read_timeout_ms
        if self._read_timeout_ms is None:
            self._read_timeout_ms = 1000

    def read_card(self) -> bytes:
        return bytes(self._card_reader_obj.read_passive_target(card_baud=self._card_baud, timeout=self._read_timeout_ms))
