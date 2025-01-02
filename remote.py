from fabric import Connection, Config
import logging
import time

RAC_IP = "ras.torizon.io"


class Remote:
    def __init__(self, dut, env_vars):
        self._logger = logging.getLogger(__name__)

        if env_vars["USE_RAC"]:
            dut.setup_rac_session(RAC_IP)
        else:
            dut.setup_usual_ssh_session()

        self.address = dut.remote_session_ip
        self.port = dut.remote_session_port
        self._password = env_vars["DEVICE_PASSWORD"]
        self._config = Config(overrides={"sudo": {"password": self._password}})
        self.connection = Connection(
            host=self.address,
            user="torizon",
            port=self.port,
            config=self._config,
            connect_timeout=15,
            connect_kwargs={
                "password": self._password,
                "banner_timeout": 60,
                "allow_agent": True,
                "look_for_keys": True,
            },
        )

        if self.test_connection():
            self._logger.debug(
                f"Connection test succeeded for device {dut.uuid}"
            )
        else:
            self._logger.error(f"Connection test failed for device {dut.uuid}")
            raise ConnectionError(
                f"Failed to establish connection with device {dut.uuid}"
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

            time.sleep(sleep_time * (tries + 1))

        self._logger.error("Remote connection test failed")
        return False
