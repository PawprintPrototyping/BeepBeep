"""
Websockets client for micropython

Based very heavily off
https://github.com/aaugustin/websockets/blob/master/websockets/client.py
"""

import usocket as socket
import ubinascii as binascii
import urandom as random
import ssl
import json
import ulogging

from networking.uwebsockets.protocol import Websocket, urlparse, URI

logger = ulogging.get_logger("websocket")

class WebsocketClient(Websocket):
    is_client = True

    def __init__(self, endpoint: str, api_key: str):
        super().__init__()
        self._endpoint: URI = urlparse(endpoint)
        self._api_key: str = api_key

    def _send_header(self, header_data: bytes, *args) -> None:
        self._sock.write(header_data % args + "\r\n")

    def connect(self, local_ip: str) -> None:
        """
        Connect a websocket.
        """

        logger.debug(f"Open websocket connection {self._endpoint.hostname}:{self._endpoint.port}")

        self._sock = socket.socket()
        addr = socket.getaddrinfo(self._endpoint.hostname, self._endpoint.port)
        logger.debug(f"Connecting to {addr[0][4]}...")
        self._sock.connect(addr[0][4])
        if self._endpoint.protocol == "wss":
            self._sock = ssl.wrap_socket(self._sock, server_hostname=self._endpoint.hostname)
        self.open = True

        # Sec-WebSocket-Key is 16 bytes of random base64 encoded
        key = binascii.b2a_base64(bytes(random.getrandbits(8) for _ in range(16)))[:-1]

        self._send_header(b"GET %s HTTP/1.1", self._endpoint.path or "/")
        self._send_header(b"Host: %s:%s", self._endpoint.hostname, self._endpoint.port)
        self._send_header(b"Connection: Upgrade")
        self._send_header(b"Upgrade: websocket")
        self._send_header(b"Sec-WebSocket-Key: %s", key)
        self._send_header(b"Sec-WebSocket-Version: 13")
        self._send_header(
            b"Origin: http://{hostname}:{port}".format(hostname=self._endpoint.hostname, port=self._endpoint.port)
        )
        self._send_header(b"")

        header = self._sock.readline()[:-2]
        assert header.startswith(
            b"HTTP/1.1 101 "
        ), "Invalid websocket header from server: " + str(header)

        # We don't (currently) need these headers
        # FIXME: should we check the return key?
        while header:
            logger.debug(str(header))
            header = self._sock.readline()[:-2]

        auth_packet = {
            "command": "authenticate",
            "secret_key": f"{self._api_key}"
        }
        logger.debug("Authenticating...")
        self.send_str(json.dumps(auth_packet))
        ip_packet = {"command": "ip_address", "ip_address": local_ip}
        self.send_str(json.dumps(ip_packet))

    @property
    def connected(self) -> bool:
        return self.open