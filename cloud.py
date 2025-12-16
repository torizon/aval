import logging
import toml
import re
from datetime import datetime
import email.utils

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

    def refresh_packages(self, release_type, hardware_id):
        delegation_prefix = None
        namespace = None

        self._log.info("Refreshing package source")

        for filter_entry in self._config["delegation_filter"]["filter"]:
            if re.search(filter_entry["hardware_id_pattern"], hardware_id):
                namespace = filter_entry["namespace"]

                if namespace in ("torizon", "torizon-upstream"):
                    delegation_prefix = "tdx"
                elif namespace == "common-torizon":
                    delegation_prefix = "common-torizon"
                break

        if not delegation_prefix:
            raise Exception(
                f"Couldn't find delegation_prefix for hardware_id={hardware_id}"
            )

        if release_type == "release":
            delegation_release_type = "quarterly"
        elif release_type in ("monthly", "nightly"):
            delegation_release_type = release_type
        else:
            # FIXME: allow refreshing custom delegations.
            # This is not needed right now, but if customers ever need it, it's
            # simple enough to implement.
            raise Exception(
                f"Refresh of {release_type} packages is not supported"
            )

        external_source = f"{delegation_prefix}-{delegation_release_type}"
        self._log.debug(f"external_source: {external_source}")

        try:
            info = endpoint_call(
                url=API_BASE_URL + "/packages_external/info",
                request_type="get",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "accept": "*/*",
                },
            )
        except Exception as e:
            self._log.error(
                f"Failed to fetch external package sources info: {e}"
            )
            return

        info_json = info.json()

        self._log.debug("Received /packages_external/info response")
        self._log.debug(f"info_json content: {info_json}")

        if external_source not in info_json:
            self._log.error(
                f"Target external source {external_source} not found in /packages_external/info. Available sources: {list(info_json.keys())}"
            )
            return

        source_data = info_json[external_source]
        self._log.debug(f"Source data: {source_data}")

        try:
            remote_uri = source_data["remoteUri"]
            last_fetched = source_data["lastFetched"]
        except KeyError as e:
            self._log.error(
                f"Missing expected key {e} in source {external_source} data: {source_data}"
            )
            return

        self._log.info(
            f"Source {external_source} - lastFetched={last_fetched} remoteUri={remote_uri}"
        )

        self._log.debug(f"Sending HEAD request to {remote_uri}")
        try:
            head = endpoint_call(
                url=remote_uri,
                request_type="head",
            )
        except Exception as e:
            self._log.error(
                f"Failed to fetch HEAD for source {external_source} ({remote_uri}): {e}"
            )
            return

        last_modified = head.headers.get("Last-Modified")
        self._log.info(
            f"HEAD response for {external_source} - Last-Modified={last_modified}"
        )

        if not last_modified:
            self._log.warning(
                f"No Last-Modified header for source {external_source}, skipping refresh check"
            )
            return

        try:
            lm_dt = email.utils.parsedate_to_datetime(last_modified)
            lf_dt = datetime.fromisoformat(last_fetched.replace("Z", "+00:00"))
        except Exception as e:
            self._log.error(
                f"Failed to parse dates for source {external_source}: lastFetched={last_fetched} Last-Modified={last_modified} error={e}"
            )
            return

        self._log.debug(
            f"Parsed dates for {external_source} - lastFetched={lf_dt} lastModified={lm_dt}"
        )

        if lm_dt > lf_dt:
            self._log.info(
                f"External source {external_source} is outdated (Last-Modified > lastFetched), triggering refresh"
            )

            refresh_url = (
                f"{API_BASE_URL}/packages_external/refresh/{external_source}"
            )
            self._log.debug(f"Calling refresh endpoint: {refresh_url}")

            try:
                refresh = endpoint_call(
                    url=refresh_url,
                    request_type="get",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "accept": "*/*",
                    },
                )
            except Exception as e:
                self._log.error(
                    f"Failed to refresh external source {external_source}: {e}"
                )
                return

            self._log.info(
                f"Refresh triggered for source {external_source}, status={getattr(refresh, 'status_code', 'unknown')}"
            )
        else:
            self._log.info(
                f"External source {external_source} is up to date, no refresh needed"
            )

        self._log.info(
            f"Finished processing external package source: {external_source}"
        )

    def get_latest_build(self, release_type, hardware_id):
        self.refresh_packages(release_type, hardware_id)

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
