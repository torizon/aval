import datetime
import dateutil
import json
import requests
import logging
import time

from cloud import CloudAPI
from http_wrapper import endpoint_call

API_BASE_URL = "https://app.torizon.io/api/v2beta"


class Device:
    def __init__(self, cloud_api: CloudAPI, uuid, hardware_id, public_key):
        self._log = logging.getLogger(__name__)

        logging.debug(f"Initializing Device object {hardware_id} for {uuid}")

        self._cloud_api = cloud_api
        self._hardware_id = hardware_id
        self._public_key = public_key
        self._current_build = None
        self._latest_build = None
        self._remote_session_time = None

        self.uuid = uuid
        self.network_info = self._get_network_info()
        self.architecture = None
        self.remote_session_ip = None
        self.remote_session_port = None

    def setup_usual_ssh_session(self):
        self.remote_session_ip = self.network_info["localIpV4"]
        self.remote_session_port = "22"

    def setup_rac_session(self, RAC_IP):
        try:
            self.remote_session_ip = RAC_IP
            if not self.is_enough_time_in_session():
                self.refresh_remote_session()
            self.remote_session_port, self._remote_session_time = (
                self._create_remote_session()
            )
        except Exception as e:
            self._log.error(f"{e}")

    def _create_remote_session(self):
        try:
            res = endpoint_call(
                url=API_BASE_URL
                + f"/remote-access/device/{self.uuid}/sessions",
                request_type="post",
                body=None,
                headers={
                    "Authorization": f"Bearer {self._cloud_api.token}",
                    "accept": "*/*",
                    "Content-Type": "application/json",
                },
                json_data={
                    "public_keys": [
                        f"{self._public_key}\n",
                    ],
                    "session_duration": "43200s",
                },
            )

        except Exception as e:
            if res and res.status_code == 409:
                self._log.info(
                    "409 Conflict: Session already exists, attempting to retrieve existing session."
                )
                return self._get_remote_session()
            logging.error(e)
        return self._get_remote_session()

    def _get_remote_session(self):
        res = endpoint_call(
            url=API_BASE_URL + f"/remote-access/device/{self.uuid}/sessions",
            request_type="get",
            body=None,
            headers={
                "Authorization": f"Bearer {self._cloud_api.token}",
                "accept": "application/json",
            },
            json_data=None,
        )
        if res is None:
            raise Exception("Failed to get remote session")

        self._log.info(
            f'Remote session created for {self.uuid} on port {res.json()["ssh"]["reverse_port"]} expiring at {res.json()["ssh"]["expires_at"]}'
        )
        return res.json()["ssh"]["reverse_port"], dateutil.parser.parse(
            res.json()["ssh"]["expires_at"]
        )

    def is_enough_time_in_session(self, time=60 * 30):
        if not self._remote_session_time:
            self._log.debug("Session expired or not enough time remaining")
            return False
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
            _ = endpoint_call(
                url=API_BASE_URL
                + f"/remote-access/device/{self.uuid}/sessions",
                request_type="delete",
                body=None,
                headers={
                    "Authorization": f"Bearer {self._cloud_api.token}",
                    "accept": "*/*",
                },
            )

            self._log.info("Remote session deleted")
            self.remote_session_port, self._remote_session_time = (
                self._create_remote_session()
            )

        except requests.RequestException as e:
            self._log.error(
                f"Request exception occurred during remote session deletion for {self.uuid}: {str(e)}"
            )

    def get_current_build(self):
        metadata = self._cloud_api.get_package_metadata_for_device(self.uuid)
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

        raise Exception(f"Couldn't parse the current build for {self.uuid}")

    def launch_update(self, build):
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._cloud_api.token}",
            "Content-Type": "application/json",
        }
        data = {
            "packageIds": [build],
            "devices": [self.uuid],
        }

        res = endpoint_call(
            url=API_BASE_URL + "/updates",
            request_type="post",
            body=None,
            headers=headers,
            json_data=data,
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
                f"Device {self.uuid} is already on latest build {current_build}"
            )
            return True
        return False

    def update_to_latest(self, target_build_type):
        logging.info(f"Refreshing {target_build_type} delegation")
        logging.info(f"Launching update to {self._latest_build}")
        self.launch_update(self._latest_build)
        logging.info("Waiting until update is complete...")

        inflight = self._cloud_api.extract_in_flight(
            self._cloud_api.get_assigment_status_for_device(self.uuid)
        )

        while inflight is not True:
            inflight = self._cloud_api.extract_in_flight(
                self._cloud_api.get_assigment_status_for_device(self.uuid)
            )
            time.sleep(15)

        logging.info(
            "The device has seen the update request and will download and install it now"
        )
        while self._cloud_api.get_assigment_status_for_device(self.uuid) != []:
            logging.info("Still updating...")
            time.sleep(60)

    def _get_network_info(self):
        res = endpoint_call(
            url=API_BASE_URL + f"/devices/network/{self.uuid}",
            request_type="get",
            body=None,
            headers={
                "Authorization": f"Bearer {self._cloud_api.token}",
                "accept": "application/json",
            },
            json_data=None,
        )
        if res is None:
            raise Exception("Failed to get network info")

        self._log.info(f"Obtained network info for {self.uuid}")
        return res.json()
