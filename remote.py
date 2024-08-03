from fabric import Connection, Config

import logging
import time


class Remote:
    def __init__(self, address, port, password):
        self._logger = logging.getLogger(__name__)
        self.address = address
        self._password = password
        self._config = Config(overrides={"sudo": {"password": password}})
        self.connection = Connection(
            host=address,
            user="torizon",
            port=port,
            config=self._config,
            connect_timeout=15,
            connect_kwargs={
                "password": password,
                "banner_timeout": 60,
                "allow_agent": True,
                "look_for_keys": True,
            },
        )

    def test_connection(self, sleep_time=3):
        for tries in range(5):
            try:
                res = self.connection.run("true", warn=True, hide=True)
                if res.exited == 0:
                    self._logger.info("Remote connection test OK")
                    return True
                else:
                    self._logger.error(
                        f"Testing remote connection failed on try {tries}. Retrying"
                    )
            except Exception as e:
                self._logger.error(
                    f"Exception occurred while testing remote connection on try {tries}: {str(e)}"
                )

            time.sleep(sleep_time * (0 + 1))

        self._logger.error("Remote connection test failed")
        return False
