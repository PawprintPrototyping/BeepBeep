"""
Websockets client for micropython

Based very heavily off
https://github.com/aaugustin/websockets/blob/master/websockets/client.py
"""

import ulogging
import usocket as socket
import ubinascii as binascii
import urandom as random
import ssl

from .protocol import Websocket, urlparse

LOGGER = ulogging.getLogger(__name__)

class WebsocketClient(Websocket):
    is_client = True

    def _send_header(self, header_data: bytes, *args) -> None:
        if __debug__:
            LOGGER.debug(str(header_data))
        self._sock.write(header_data % args + "\r\n")

    def connect(self, uri: str) -> None:
        """
        Connect a websocket.
        """

        uri = urlparse(uri)

        if __debug__:
            LOGGER.debug("open connection %s:%s", uri.hostname, uri.port)

        self._sock = socket.socket()
        addr = socket.getaddrinfo(uri.hostname, uri.port)
        self._sock.connect(addr[0][4])
        if uri.protocol == "wss":
            self._sock = ssl.wrap_socket(self._sock)

        # Sec-WebSocket-Key is 16 bytes of random base64 encoded
        key = binascii.b2a_base64(bytes(random.getrandbits(8) for _ in range(16)))[:-1]

        self._send_header(b"GET %s HTTP/1.1", uri.path or "/")
        self._send_header(b"Host: %s:%s", uri.hostname, uri.port)
        self._send_header(b"Connection: Upgrade")
        self._send_header(b"Upgrade: websocket")
        self._send_header(b"Sec-WebSocket-Key: %s", key)
        self._send_header(b"Sec-WebSocket-Version: 13")
        self._send_header(
            b"Origin: http://{hostname}:{port}".format(hostname=uri.hostname, port=uri.port)
        )
        self._send_header(b"")

        header = self._sock.readline()[:-2]
        assert header.startswith(
            b"HTTP/1.1 101 "
        ), "Invalid websocket header from server: " + str(header)

        # We don't (currently) need these headers
        # FIXME: should we check the return key?
        while header:
            if __debug__:
                LOGGER.debug(str(header))
            header = self._sock.readline()[:-2]