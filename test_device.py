import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
import requests
import logging
from cloud import CloudAPI
from device import Device


class TestDevice(unittest.TestCase):

    def setUp(self):
        self.mock_cloud_api = MagicMock(spec=CloudAPI)
        self.mock_cloud_api.token = "dummy_token"

        self.mock_response_post = MagicMock(spec=requests.Response)
        self.mock_response_post.status_code = 200
        self.mock_response_post.json.return_value = {
            "ssh": {
                "reverse_port": 3333,
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(hours=12)
                ).isoformat(),
            }
        }

        self.mock_response_get = MagicMock(spec=requests.Response)
        self.mock_response_get.status_code = 200
        self.mock_response_get.json.return_value = (
            self.mock_response_post.json.return_value
        )

        self.mock_response_delete = MagicMock(spec=requests.Response)
        self.mock_response_delete.status_code = 200

        self.patcher_post = patch(
            "requests.post", return_value=self.mock_response_post
        )
        self.patcher_get = patch(
            "requests.get", return_value=self.mock_response_get
        )
        self.patcher_delete = patch(
            "requests.delete", return_value=self.mock_response_delete
        )

        self.mocked_post = self.patcher_post.start()
        self.mocked_get = self.patcher_get.start()
        self.mocked_delete = self.patcher_delete.start()

        logging.disable(logging.CRITICAL)

    def tearDown(self):
        self.patcher_post.stop()
        self.patcher_get.stop()
        self.patcher_delete.stop()

        logging.disable(logging.NOTSET)

    def test_create_remote_session_success(self):
        current_time = datetime.now(timezone.utc)
        expires_at = (current_time + timedelta(hours=12)).isoformat()

        self.mock_response_post.json.return_value = {
            "ssh": {
                "reverse_port": 2222,
                "expires_at": expires_at,
            }
        }

        self.mock_response_get.json.return_value = (
            self.mock_response_post.json.return_value
        )

        device = Device(self.mock_cloud_api, "dummy_uuid", "dummy_public_key")

        self.assertEqual(device.remote_session_port, 2222)
        self.assertTrue(device.is_enough_time_in_session())
        self.assertIsNotNone(device._remote_session_time)

        self.mocked_post.assert_called_once()
        self.mocked_get.assert_called_once()

    def test_refresh_remote_session_success(self):
        self.mock_response_delete.status_code = 200

        self.mock_response_post.json.return_value = {
            "ssh": {
                "reverse_port": 3333,
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(hours=12)
                ).isoformat(),
            }
        }

        self.mock_response_get.json.return_value = (
            self.mock_response_post.json.return_value
        )

        dummy_uuid = "dummy_uuid"

        device = Device(self.mock_cloud_api, dummy_uuid, "dummy_public_key")

        device.refresh_remote_session()

        self.mocked_delete.assert_called_once_with(
            f"https://app.torizon.io/api/v2beta/remote-access/device/{dummy_uuid}/sessions",
            headers={
                "Authorization": f"Bearer dummy_token",
                "accept": "*/*",
            },
        )

        self.assertTrue(device.remote_session_port == 3333)
        self.assertTrue(device.is_enough_time_in_session())
        self.assertIsNotNone(device._remote_session_time)

        """
        the endpoint `sessions` is actually called twice in
        `refresh_remote_session`: once to delete a current session and a second
        time in `_create_remote_session` to get another one. 
        """
        self.assertEqual(self.mocked_post.call_count, 2)
        self.assertEqual(self.mocked_get.call_count, 2)

    def test_refresh_remote_session_failure(self):
        self.mock_response_delete.status_code = 500

        dummy_uuid = "dummy_uuid"

        device = Device(self.mock_cloud_api, dummy_uuid, "dummy_public_key")

        with self.assertRaises(Exception):
            device.refresh_remote_session()

        self.mocked_delete.assert_called_once_with(
            f"https://app.torizon.io/api/v2beta/remote-access/device/{dummy_uuid}/sessions",
            headers={
                "Authorization": f"Bearer dummy_token",
                "accept": "*/*",
            },
        )

        # the endpoint will be called once during the `device` object construction
        self.mocked_post.assert_called_once()
        self.mocked_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
