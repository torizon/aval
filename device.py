import datetime
import dateutil
import json
import requests
import logging

from cloud import CloudAPI

API_BASE_URL = "https://app.torizon.io/api/v2beta"


class Device:
    def __init__(self, cloud_api: CloudAPI, uuid, public_key):
        self._log = logging.getLogger(__name__)
        self._cloud_api = cloud_api
        self._uuid = uuid
        self._public_key = public_key
        self._remote_session_port, self._remote_session_time = (
            self._create_remote_session()
        )
        if not self.is_enough_time_in_session():
            self.refresh_remote_session()

    @property
    def remote_session_port(self):
        return self._remote_session_port

    def _create_remote_session(self):
        res = requests.post(
            API_BASE_URL + f"/remote-access/device/{self._uuid}/sessions",
            headers={
                "Authorization": f"Bearer {self._cloud_api.token}",
                "accept": "*/*",
                "Content-Type": "application/json",
            },
            json={
                "public_keys": [
                    f"{self._public_key}\n",
                ],
                "session_duration": "43200s",
            },
        )

        if res.status_code != 200 and res.status_code != 409:
            self._log.error(
                f"Error: could not create remote session on {self._uuid}, error: {res.status_code}"
            )
            self._log.error(json.dumps(res.json(), indent=2))
            return None, None

        res = requests.get(
            API_BASE_URL + f"/remote-access/device/{self._uuid}/sessions",
            headers={
                "Authorization": f"Bearer {self._cloud_api.token}",
                "accept": "application/json",
            },
        )

        if res.status_code != 200:
            self._log.error(
                f"Error: could not retrieve remote session on {self._uuid}, error: {res.status_code}"
            )
            self._log.error(json.dumps(res.json(), indent=2))
            return None, None

        self._log.info(
            f'Remote session created for {self._uuid} on port {res.json()["ssh"]["reverse_port"]} expiring at {res.json()["ssh"]["expires_at"]}'
        )
        return res.json()["ssh"]["reverse_port"], dateutil.parser.parse(
            res.json()["ssh"]["expires_at"]
        )

    def get_remote_port(self):
        self._log.debug(self._remote_session_port)
        return self._remote_session_port

    def is_enough_time_in_session(self, time=60 * 30):
        remaining_time = (
            self._remote_session_time
            - datetime.datetime.now().astimezone(datetime.timezone.utc)
        )
        if remaining_time.days == 0 and remaining_time.seconds > time:
            self._log.debug("Theres enough time is session")
            return True

        # if not enough time left (expired or <30m left), we need to delete existing connection and create a new one
        self._log.debug("Session expired or not enough time remaining")
        return False

    def refresh_remote_session(self):
        try:
            res = requests.delete(
                API_BASE_URL + f"/remote-access/device/{self._uuid}/sessions",
                headers={
                    "Authorization": f"Bearer {self._cloud_api.token}",
                    "accept": "*/*",
                },
            )
            if res.status_code != 200:
                self._log.error(
                    f"Error: could not delete remote session on {self._uuid}, error: {res.status_code}"
                )
                self._log.error(json.dumps(res.json(), indent=2))
                return

            self._log.info("Remote session deleted")
            self._remote_session_port, self._remote_session_time = (
                self._create_remote_session()
            )

        except requests.RequestException as e:
            self._log.error(
                f"Request exception occurred during remote session deletion for {self._uuid}: {str(e)}"
            )
