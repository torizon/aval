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
        try:
            self._remote_session_port, self._remote_session_time = (
                self._create_remote_session()
            )
            if not self.is_enough_time_in_session():
                self.refresh_remote_session()
        except Exception as e:
            self._log.error(
                f"Fail to create remote session for device with uuid {self._uuid}"
            )

    @property
    def remote_session_port(self):
        return self._remote_session_port

    def _create_remote_session(self):
        try:
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
            res.raise_for_status()
            error_message = None
        except requests.exceptions.HTTPError as errh:
            if res.status_code == 409:
                self._log.info(
                    f"409 Conflict: Session already exists, attempting to retrieve existing session."
                )
                return self._get_remote_session()
            error_message = f"Http Error: {errh}"
        except requests.exceptions.ConnectionError as errc:
            error_message = f"Error Connecting: {errc}"
        except requests.exceptions.Timeout as errt:
            error_message = f"Timeout Error: {errt}"
        except requests.exceptions.RequestException as err:
            error_message = f"Oops: Something Else: {err}"
        else:
            error_message = None

        if error_message:
            try:
                self._log.info(json.dumps(res.json(), indent=2))
            except json.JSONDecodeError as e:
                self._log.error(f"Error decoding JSON response: {e}")
            self._log.error(error_message)
            raise Exception(error_message)

        return self._get_remote_session()

    def _get_remote_session(self):
        try:
            res = requests.get(
                API_BASE_URL + f"/remote-access/device/{self._uuid}/sessions",
                headers={
                    "Authorization": f"Bearer {self._cloud_api.token}",
                    "accept": "application/json",
                },
            )

            res.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            error_message = f"Http Error: {errh}"
        except requests.exceptions.ConnectionError as errc:
            error_message = f"Error Connecting: {errc}"
        except requests.exceptions.Timeout as errt:
            error_message = f"Timeout Error: {errt}"
        except requests.exceptions.RequestException as err:
            error_message = f"Oops: Something Else: {err}"
        else:
            error_message = None

        if error_message:
            try:
                self._log.error(json.dumps(res.json(), indent=2))
            except json.JSONDecodeError as e:
                self._log.error(f"Error decoding JSON response: {e}")
            self._log.error(error_message)
            raise Exception(error_message)

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
