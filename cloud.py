import logging
import toml
import re

from http_wrapper import endpoint_call

API_BASE_URL = "https://app.torizon.io/api/v2"


class CloudAPI:

    def __init__(self, api_client, api_secret, delegation_config_path):
        self._log = logging.getLogger(__name__)

        self.api_client = api_client
        self.api_secret = api_secret

        self._config = toml.load(delegation_config_path)

        self.token = self._get_bearer_token()[0]
        self.provisioned_devices = self._get_provisioned_devices()

    def _get_bearer_token(self):
        tokens = []
        res = endpoint_call(
            url="https://kc.torizon.io/auth/realms/ota-users/protocol/openid-connect/token",
            request_type="post",
            body={
                "grant_type": "client_credentials",
                "client_id": self.api_client,
                "client_secret": self.api_secret,
            },
            headers=None,
            json_data=None,
        )

        tokens.append(res.json()["access_token"])

        self._log.debug("API tokens generated.")
        return tuple(tokens)

    def _get_provisioned_devices(self):
        res = endpoint_call(
            url=API_BASE_URL + "/devices",
            request_type="get",
            body=None,
            headers={
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            },
            json_data=None,
        )

        if self._log.isEnabledFor(logging.DEBUG):
            self._log.debug(res.json()["values"])
        self._log.debug("Got provisioned devices on platform")
        return res.json()["values"]

    def get_latest_build(self, release_type, hardware_id):
        for filter_entry in self._config["delegation_filter"]["filter"]:
            if re.search(filter_entry["hardware_id_pattern"], hardware_id):
                name_prefix = filter_entry["name_prefix"]
                namespace = filter_entry["namespace"]
                name_suffix = filter_entry["name_suffix"]

                name_contains = f"{name_prefix}/{hardware_id}/{namespace}/{name_suffix}/{release_type}"
                break

        url = (
            API_BASE_URL
            + f"/packages?nameContains={name_contains}&hardwareIds={hardware_id}&sortBy=Filename&sortDirection=Desc"
        )

        res = endpoint_call(
            url,
            request_type="get",
            body=None,
            headers={
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            },
            json_data=None,
        )

        if self._log.isEnabledFor(logging.DEBUG):
            self._log.debug(res.json()["values"])

        latest_build = next(
            (item["packageId"] for item in res.json().get("values", [])), None
        )
        if latest_build:
            self._log.info(f"Latest build is {latest_build}")
            return latest_build
        else:
            raise Exception(
                f"Couldn't parse the latest build for {release_type} with {hardware_id}"
            )

    def get_package_metadata_for_device(self, uuid):
        res = endpoint_call(
            url=API_BASE_URL + f"/devices/packages?deviceUuid={uuid}",
            request_type="get",
            body=None,
            headers={
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            },
            json_data=None,
        )

        if self._log.isEnabledFor(logging.DEBUG):
            self._log.debug(res.json()["values"])
        self._log.info(f"Got package metadata for device {uuid}")
        return res.json()["values"]

    def extract_in_flight(self, data):
        for item in data:
            return item.get("inFlight")

    def get_assigment_status_for_device(self, uuid):
        res = endpoint_call(
            url=f"{API_BASE_URL}/devices/uptane/{uuid}/assignment",
            request_type="get",
            body=None,
            headers={
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            },
            json_data=None,
        )

        if self._log.isEnabledFor(logging.DEBUG):
            self._log.debug(res.json())
        self._log.debug(
            f"Got package update assignment status for device {uuid}"
        )
        return res.json()
