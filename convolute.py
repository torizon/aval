# The name of this module is "convolute" because "filter" is a Python keyword
# and most of us are EEs anyway.

import yaml
import toml


def get_pid4_list(soc, pid4_map):
    soc_data = pid4_map.get(soc, {})

    pid4s = soc_data.get("pid4", [])

    pid4_list = [
        pid.get("id", pid) if isinstance(pid, dict) else pid for pid in pid4s
    ]

    return pid4_list


def get_pid4_list_with_device_config(device_config, pid4_map):

    soc_udt, soc_properties = get_device_config_data(device_config)

    pid4_data = pid4_map[soc_udt]["pid4"]

    pid4_list = []

    for pid4 in pid4_data:
        if all(prop in pid4 for prop in soc_properties):
            pid4_list.append(pid4["id"])

    return pid4_list


def get_device_config_data(device_config):
    soc_udt = device_config["soc_udt"]["soc_udt_name"]
    soc_properties = device_config["soc_udt"]["soc_properties"]

    return (soc_udt, soc_properties)
