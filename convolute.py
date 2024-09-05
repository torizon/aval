# The name of this module is "convolute" because "filter" is a Python keyword
# and most of us are EEs anyway.


def get_pid4_list(soc, pid4_map):
    soc_data = pid4_map.get(soc, {})

    pid4s = soc_data.get("pid4", [])

    pid4_list = [
        pid.get("id", pid) if isinstance(pid, dict) else pid for pid in pid4s
    ]

    return pid4_list
