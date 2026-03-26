from prettytable import PrettyTable
import config_loader
import logging_setup

logger = logging_setup.setup_logging()


def parse_device_id(device_id):
    parts = device_id.split("-")
    return parts[1] if len(parts) > 1 else None


def parse_hardware_id(device_id):
    parts = device_id.split("-")
    if "emmc" in device_id or "smarc" in device_id:
        return parts[0] + "-" + parts[1] + "-" + parts[2]
    elif "imx93frdm" in device_id:
        return parts[0]
    elif "torizon-x86" in device_id:
        return "intel-corei7-64"
    elif "torizon-sl1680" in device_id:
        return parts[1]
    elif "torizon" in device_id:
        return parts[1] + "-" + parts[2]
    else:
        return parts[0] + "-" + parts[1]


def pretty_print_devices(devices):
    table = PrettyTable(["Device UUID", "Device Name"])
    for device in devices:
        table.add_row([device["deviceUuid"], device["deviceName"]])

    table_string = table.get_string()
    for line in table_string.split("\n"):
        logger.info(line)


def get_architectures_from_pid_map(pid_map):
    pid4_map = config_loader.load_pid_map(pid_map_path=pid_map)

    return {
        pid["architecture"]
        for machine in pid4_map.values()
        if isinstance(machine, dict)
        for pid in machine.get("pid4", [])
        if isinstance(pid, dict) and pid.get("architecture")
    }
