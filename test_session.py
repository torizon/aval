import unittest
from unittest.mock import patch, MagicMock
import datetime
from device import Device


class TestDeviceInitialization(unittest.TestCase):
    @patch("device.Device._create_remote_session")
    @patch("device.endpoint_call")
    def test_initialization_refresh_called(
        self,
        mock_endpoint_call,
        mock_create_remote_session,
    ):
        mock_endpoint_call.return_value = MagicMock()
        mock_endpoint_call.return_value.json.return_value = {
            "network_info": "dummy_data"
        }

        mock_cloud_api = MagicMock()
        mock_cloud_api.token = "test-token"

        mock_create_remote_session.return_value = (
            1234,
            datetime.datetime(
                2024, 7, 26, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )

        env_vars = {
            "DEVICE_PASSWORD": "secret",
            "PUBLIC_KEY": "ssh-rsa",
        }

        device = Device(
            cloud_api=mock_cloud_api,
            uuid="test-uuid",
            hardware_id="test-hardware-id",
            env_vars=env_vars,
        )

        mock_create_remote_session.assert_not_called()

        self.assertEqual(device.remote_session_port, None)
        self.assertEqual(device._remote_session_time, None)

    @patch("device.Device._create_remote_session")
    @patch(
        "device.endpoint_call"
    )  # Mock endpoint_call to avoid actual network calls
    def test_initialization_no_refresh_called(
        self,
        mock_endpoint_call,
        mock_create_remote_session,
    ):
        mock_endpoint_call.return_value = MagicMock()
        mock_endpoint_call.return_value.json.return_value = {
            "network_info": "dummy_data"
        }

        mock_cloud_api = MagicMock()
        mock_cloud_api.token = "test-token"

        mock_create_remote_session.return_value = (
            1234,
            datetime.datetime(
                2024, 7, 26, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )

        env_vars = {
            "DEVICE_PASSWORD": "secret",
            "PUBLIC_KEY": "ssh-rsa",
        }

        device = Device(
            cloud_api=mock_cloud_api,
            uuid="test-uuid",
            hardware_id="test-hardware-id",
            env_vars=env_vars,
        )

        mock_create_remote_session.assert_not_called()

        self.assertEqual(device.remote_session_port, None)
        self.assertEqual(device._remote_session_time, None)
