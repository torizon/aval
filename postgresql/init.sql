CREATE TABLE IF NOT EXISTS devices (
    device_uuid UUID PRIMARY KEY,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    "timestamp" timestamptz
);
