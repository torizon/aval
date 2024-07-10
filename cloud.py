import datetime
import requests
import logging
import dateutil
import json
import time

API_BASE_URL = "https://app.torizon.io/api/v2beta"


class CloudAPI:

    def __init__(self, api_client, api_secret):
        self._log = logging.getLogger(__name__)

        self.api_client = api_client
        self.api_secret = api_secret

        self.token = self._get_bearer_token()[0]
        self.provisioned_devices = self._get_provisioned_devices()

    def _get_bearer_token(self):
        tokens = []
        res = requests.post(
            "https://kc.torizon.io/auth/realms/ota-users/protocol/openid-connect/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.api_client,
                "client_secret": self.api_secret,
            },
        )

        if res.status_code != 200:
            self._log.error(
                f"Could not retrieve API token, error: {res.status_code}"
            )
            self._log.error(json.dumps(res.json(), indent=2))
            return None, None

        tokens.append(res.json()["access_token"])

        self._log.debug("API tokens generated.")
        return tuple(tokens)

    def _get_provisioned_devices(self):
        res = requests.get(
            API_BASE_URL + "/devices",
            headers={
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            },
        )

        if res.status_code != 200:
            self._log.error(
                f"Error: could not retrieve provisioned devices, error: {res.status_code}"
            )
            self._log.error(json.dumps(res.json(), indent=2))
            return None

        if self._log.isEnabledFor(logging.DEBUG):
            self._log.debug(res.json()["values"])
        self._log.debug("Got provisioned devices on platform")
        return res.json()["values"]

    def _refresh_delegation(
        self, delegation, max_retries=3, backoff_factor=10.0
    ):
        for attempt in range(max_retries):
            try:
                res = requests.get(
                    API_BASE_URL + f"/packages_external/refresh/{delegation}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "accept": "*/*",
                        "Content-Type": "application/json",
                    },
                )
                res.raise_for_status()
                return
            except requests.exceptions.HTTPError as errh:
                if res.status_code == 503:
                    self._log.warning(
                        f"503 Service Unavailable, retrying... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(backoff_factor * (2**attempt))
                    continue
                else:
                    error_message = f"HTTP Error: {errh}"
            except requests.exceptions.ConnectionError as errc:
                error_message = f"Error Connecting: {errc}"
                break
            except requests.exceptions.Timeout as errt:
                error_message = f"Timeout Error: {errt}"
                break
            except requests.exceptions.RequestException as err:
                error_message = f"Oops: Something Else: {err}"
                break
        else:
            error_message = "Max retries exceeded"

        self._log.error(error_message)
        try:
            self._log.info(json.dumps(res.json(), indent=2))
        except json.JSONDecodeError as e:
            self._log.error(f"Error decoding JSON response: {e}")
        raise Exception(error_message)

    def get_latest_build(self, release_type, hardware_id):
        # upstream images get a different namespace for some reason now long forgotten.
        if "imx6" in hardware_id or "imx7" in hardware_id:
            name_contains = f"kirkstone/{hardware_id}/torizon-upstream/torizon-core-docker/{release_type}"
        else:
            name_contains = f"kirkstone/{hardware_id}/torizon/torizon-core-docker/{release_type}"

        url = (
            API_BASE_URL
            + f"/packages?nameContains={name_contains}&hardwareIds={hardware_id}&sortBy=Filename&sortDirection=Desc"
        )

        res = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            },
        )

        if res.status_code != 200:
            self._log.error(
                f"Error: could not retrieve package metadata, error: {res.status_code}"
            )
            self._log.error(json.dumps(res.json(), indent=2))
            return None

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
        res = requests.get(
            API_BASE_URL + f"/devices/packages?deviceUuid={uuid}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            },
        )

        if res.status_code != 200:
            self._log.error(
                f"Error: could not retrieve package metadata for device {uuid}, error: {res.status_code}"
            )
            self._log.error(json.dumps(res.json(), indent=2))
            return None

        if self._log.isEnabledFor(logging.DEBUG):
            self._log.debug(res.json()["values"])
        self._log.info(f"Got package metadata for device {uuid}")
        return res.json()["values"]

    def extract_in_flight(self, data):
        for item in data:
            return item.get("inFlight")

    def get_assigment_status_for_device(self, uuid):
        res = requests.get(
            f"{API_BASE_URL}/devices/uptane/{uuid}/assignment",
            headers={
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            },
        )

        if res.status_code != 200:
            self._log.error(
                f"Error: could not retrieve update assignment status for device {uuid}, error: {res.status_code}"
            )
            self._log.error(res)
            return None

        if self._log.isEnabledFor(logging.DEBUG):
            self._log.debug(res.json())
        self._log.debug(
            f"Got package update assignment status for device {uuid}"
        )
        return res.json()
