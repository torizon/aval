def parse_device_id(device_id):
    parts = device_id.split("-")
    return parts[1] if len(parts) > 1 else None
