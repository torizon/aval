import toml
import yaml
import os


def load_device_config(device_config_path):
    return toml.load(device_config_path)


def load_pid_map(pid_map_path=None):
    if not pid_map_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pid_map_path = os.path.join(script_dir, "pid_map.yaml")

    with open(pid_map_path, "r") as f:
        return yaml.safe_load(f)
