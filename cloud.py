import datetime
import requests
import logging
import dateutil
import json

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

        if tokens[0] == None:
            self._log.info("No API info specified for the new Cloud account")
        self._log.info("API tokens generated.")
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
        self._log.info("Got provisioned devices on platform")
        return res.json()["values"]

    def get_provisioned_uuid(self, cloud, uuid):
        for device in self.get_provisioned_devices(cloud):
            if device["deviceUuid"] == uuid:
                self._log.info(f"Found device {uuid} on Cloud {cloud}")
                return device
        self._log.info(f"Could not find device {uuid} on Cloud {cloud}")
        return None
