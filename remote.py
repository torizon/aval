from device import Device
from fabric import Connection, Config

import logging
import time


class Remote:
    def __init__(self, device: Device, address, password):
        self._logger = logging.getLogger(__name__)
        self._device = device
        self.address = address
        self._password = password
        self._config = Config(overrides={"sudo": {"password": password}})
        self.connection = Connection(
            host=address,
            user="torizon",
            port=device.remote_session_port,
            config=self._config,
            connect_timeout=15,
            connect_kwargs={
                "banner_timeout": 60,
            },
        )

    def test_connection(self):
        time.sleep(10)
        for tries in range(5):
            try:
                res = self.connection.run("true", warn=True, hide=True)
                if res.exited == 0:
                    self._logger.info("Remote connection test OK")
                    return True
                self._logger.error(
                    f"Testing remote connection failed on try {tries}. Retrying"
                )
                time.sleep(3 * tries)
            except:
                self._logger.error(
                    f"Testing remote connection failed on try {tries}. Retrying"
                )
                time.sleep(3 * tries)

        self._logger.error("Remote connection test failed")
        return False
