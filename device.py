import datetime
import dateutil
import json
import requests
import logging
import time

import common

from cloud import CloudAPI

API_BASE_URL = "https://app.torizon.io/api/v2beta"


class Device:
    def __init__(self, cloud_api: CloudAPI, uuid, hardware_id, public_key):
        self._log = logging.getLogger(__name__)
        self._cloud_api = cloud_api
        self._uuid = uuid
        self._hardware_id = hardware_id
        self._public_key = public_key
        self._current_build = None
        self._latest_build = None
        self._remote_session_port = None
        self._remote_session_time = None

        logging.debug(
            f"Initializing Device object {self._hardware_id} for {self._uuid}"
        )

        try:
            self._remote_session_port, self._remote_session_time = (
                self._create_remote_session()
            )
            if not self.is_enough_time_in_session():
                self.refresh_remote_session()
        except Exception as e:
            self._log.error(f"{e}")

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
                self._log.error(f"Error decoding JSON res: {e}")
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
                self._log.error(f"Error decoding JSON res: {e}")
            self._log.error(error_message)
            raise Exception(error_message)

        self._log.info(
            f'Remote session created for {self._uuid} on port {res.json()["ssh"]["reverse_port"]} expiring at {res.json()["ssh"]["expires_at"]}'
        )
        return res.json()["ssh"]["reverse_port"], dateutil.parser.parse(
            res.json()["ssh"]["expires_at"]
        )

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

    def get_current_build(self):
        metadata = self._cloud_api.get_package_metadata_for_device(self._uuid)
        for device in metadata:
            for pkg in device["installedPackages"]:
                logging.debug(pkg)
                logging.debug(self._hardware_id)
                if pkg["component"] == self._hardware_id:
                    current_build = pkg["installed"]["packageName"]
                    logging.info(
                        f"Current build for {self._hardware_id} is: {current_build}"
                    )
                    return current_build

        raise Exception(f"Couldn't parse the current build for {self._uuid}")

    def launch_update(self, build):
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._cloud_api.token}",
            "Content-Type": "application/json",
        }
        data = {
            "packageIds": [build],
            "custom": {
                build: {
                    "uri": "https://tzn-ota-tdxota.s3.amazonaws.com/ostree-repo/"
                }
            },
            "devices": [self._uuid],
        }

        res = requests.post(
            API_BASE_URL + "/updates", headers=headers, json=data
        )

        # FIXME: currently a bug on the Cloud side. Returns 201 when succesfull.
        if res.status_code == 200 or res.status_code == 201:
            logging.info("Updating succesfully issued.")
        else:
            logging.error(
                f"Update launch request failed with status code: {res.status_code}"
            )
            self._log.info(json.dumps(res.json(), indent=2))

        res.raise_for_status()

    def is_os_updated_to_latest(self, release_type):
        current_build = self.get_current_build()

        self._latest_build = self._cloud_api.get_latest_build(
            release_type=release_type, hardware_id=self._hardware_id
        )

        if current_build == self._latest_build:
            logging.info(
                f"Device {self._uuid} is already on latest build {current_build}"
            )
            return True
        return False

    def update_to_latest(self, target_build_type):
        logging.info(f"Refreshing {target_build_type} delegation")
        if target_build_type == "nightly":
            self._cloud_api._refresh_delegation("tdx-nightly")
        elif target_build_type == "release":
            self._cloud_api._refresh_delegation("tdx-quarterly")
        else:
            """
            FIXME: allow refreshing custom delegations.
            This is not needed right now, but if customers ever need it, it's
            simple enough to implement.
            """
            raise Exception("Found no delegation to refresh")
        logging.info(f"Launching update to {self._latest_build}")
        self.launch_update(self._latest_build)
        logging.info("Waiting until update is complete...")

        inflight = self._cloud_api.extract_in_flight(
            self._cloud_api.get_assigment_status_for_device(self._uuid)
        )

        while inflight != True:
            inflight = self._cloud_api.extract_in_flight(
                self._cloud_api.get_assigment_status_for_device(self._uuid)
            )
            time.sleep(15)

        logging.info(
            "The device has seen the update request and will download and install it now"
        )
        while self._cloud_api.get_assigment_status_for_device(self._uuid) != []:
            logging.info("Still updating...")
            time.sleep(60)
