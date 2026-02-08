from networking.wifi import WifiConnection
from config_utils import pull_str_from_config
import typing

def generate_wifi_connection(config_json: typing.Dict) -> WifiConnection:
    if "wifi" not in config_json.keys():
        raise ValueError("Network config does not have any configuration for wifi")
    wifi_config = config_json["wifi"]
    ssid = pull_str_from_config(config_json=wifi_config, key="ssid", optional=False)
    password = pull_str_from_config(config_json=wifi_config, key="password", optional=False)
    chosen_hostname = pull_str_from_config(config_json=wifi_config, key="hostname", optional=True)
    if chosen_hostname is None:
        chosen_hostname = ""
    return WifiConnection(ssid=ssid, password=password, chosen_hostname=chosen_hostname)