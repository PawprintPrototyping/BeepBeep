import typing

TRUTHY_STRINGS = ("yes", "y", "1", "make it so", "true", "ye")

def pull_str_from_config(config_json: typing.Dict[str, str], key: str, optional: bool = True) -> typing.Optional[str]:
    config_value = config_json.get(key)
    if not optional and config_value is None:
        raise ValueError(f"{key} is not set in the hardware config {config_value}")
    return config_value

def pull_int_from_config(config_json: typing.Dict[str, str], key: str, optional: bool = True) -> typing.Optional[int]:
    try:
        possible_int = pull_str_from_config(config_json=config_json, key=key, optional=optional)
        if "0x" in possible_int:
            return int(possible_int, 16)
        return int(possible_int)
    except ValueError:
        raise ValueError(f"Unable to convert {pull_str_from_config(config_json=config_json, key=key)} to int "
                         f"while reading {key} from hardware config")

def pull_bool_from_config(config_json: typing.Dict[str, str], key: str, optional: bool = True) -> typing.Optional[bool]:
    return pull_str_from_config(config_json=config_json, key=key, optional=optional).replace(" ", "").rstrip().casefold() in TRUTHY_STRINGS

