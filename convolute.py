# The name of this module is "convolute" because "filter" is a Python keyword
# and most of us are EEs anyway.

import yaml
import toml
import logging

logger = logging.getLogger(__name__)


def get_pid4_list(soc, pid4_map):
    logger.debug(f"Getting PID4 list for SOC: {soc}")

    soc_data = pid4_map.get(soc, {})
    pid4s = soc_data.get("pid4", [])

    logger.debug(f"Found PID4s: {pid4s}")
    pid4_list = [
        pid.get("id", pid) if isinstance(pid, dict) else pid for pid in pid4s
    ]

    logger.debug(f"PID4 list: {pid4_list}")

    return pid4_list


def get_pid4_list_from_architecture(soc_architecture, pid4_map):
    logger.debug(f"Getting PID4 list for architecture: {soc_architecture}")

    matching_pid4s = []
    for soc_name, soc_data in pid4_map.items():
        for pid4_entry in soc_data.get("pid4", []):
            if pid4_entry.get("architecture") == soc_architecture:
                matching_pid4s.append(pid4_entry.get("id"))

    logger.debug(f"Matching PID4 list: {matching_pid4s}")
    return matching_pid4s


def get_pid4_list_with_device_config(device_config, pid4_map):
    logger.debug("Getting PID4 list with device config")

    soc_udt, soc_properties = device_config

    pid4_data = pid4_map.get(soc_udt, {}).get("pid4", [])

    logger.debug(f"PID4 data: {pid4_data}")

    pid4_list = []
    for pid4 in pid4_data:
        if all(prop in pid4 for prop in soc_properties):
            pid4_list.append(pid4["id"])

    logger.debug(f"Filtered PID4 list: {pid4_list}")

    return pid4_list


def get_device_config_data(device_config):
    logger.debug("Getting device config data")
    logger.debug(f"Device config: {device_config}")

    soc_udt = device_config["soc_udt"]["soc_udt_name"]
    soc_properties = device_config["soc_udt"]["soc_properties"]

    logger.debug(f"SOC UDT: {soc_udt}, SOC Properties: {soc_properties}")

    return (soc_udt, soc_properties)
