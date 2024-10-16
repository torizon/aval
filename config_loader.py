import toml
import yaml


def load_device_config(device_config_path):
    return toml.load(device_config_path)


def load_pid_map(pid_map_path="pid_map.yaml"):
    with open(pid_map_path, "r") as f:
        return yaml.safe_load(f)
