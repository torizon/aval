import unittest
from unittest.mock import MagicMock, patch
from device import Device

max_attempts = 10


class TestDeviceGetCurrentBuild(unittest.TestCase):
    def setUp(self):
        self.mock_cloud_api = MagicMock()
        self.uuid = "device-uuid-1234"
        self.hardware_id = "component-x"
        self.env_vars = {
            "DEVICE_PASSWORD": "pass",
            "PUBLIC_KEY": "ssh-rsa AAAAB3Nza...",
            "USE_RAC": False,
        }

        with patch.object(
            Device, "_get_network_info", return_value={"localIpV4": "127.0.0.1"}
        ):
            self.device = Device(
                cloud_api=self.mock_cloud_api,
                uuid=self.uuid,
                hardware_id=self.hardware_id,
                env_vars=self.env_vars,
            )

    @patch("time.sleep", return_value=None)
    def test_get_current_build_success(self, _):
        expected_build = "my-build-1.2.3"

        self.mock_cloud_api.get_package_metadata_for_device.return_value = [
            {
                "installedPackages": [
                    {
                        "component": self.hardware_id,
                        "installed": {"packageId": expected_build},
                    }
                ]
            }
        ]

        result = self.device.get_current_build()
        self.assertEqual(result, expected_build)
        self.mock_cloud_api.get_package_metadata_for_device.assert_called_once_with(
            self.uuid
        )

    @patch("time.sleep", return_value=None)
    def test_get_current_build_retry_and_succeed(self, _):
        expected_build = "my-build-1.2.3"

        # First two attempts raise exception, third succeeds
        self.mock_cloud_api.get_package_metadata_for_device.side_effect = [
            Exception("API error"),
            Exception("API error again"),
            [
                {
                    "installedPackages": [
                        {
                            "component": self.hardware_id,
                            "installed": {"packageId": expected_build},
                        }
                    ]
                }
            ],
        ]

        with patch("time.sleep", return_value=None):
            result = self.device.get_current_build()

        self.assertEqual(result, expected_build)
        self.assertEqual(
            self.mock_cloud_api.get_package_metadata_for_device.call_count, 3
        )

    @patch("time.sleep", return_value=None)
    def test_get_current_build_failure_no_packages(self, _):
        self.mock_cloud_api.get_package_metadata_for_device.return_value = [{}]

        with self.assertRaises(Exception) as context:
            self.device.get_current_build()

        expected_message = f"Couldn't parse the current build for {self.device.uuid} after {max_attempts} attempts"
        self.assertIn(expected_message, str(context.exception))
        self.assertEqual(
            self.mock_cloud_api.get_package_metadata_for_device.call_count,
            max_attempts,
        )

    @patch("time.sleep", return_value=None)
    def test_get_current_build_failure_hardware_not_found(self, _):
        self.mock_cloud_api.get_package_metadata_for_device.return_value = [
            {
                "installedPackages": [
                    {
                        "component": "wrong-hardware",
                        "installed": {"packageId": "some-build"},
                    }
                ]
            }
        ]

        with self.assertRaises(Exception) as context:
            self.device.get_current_build()

        expected_message = f"Couldn't parse the current build for {self.device.uuid} after {max_attempts} attempts"
        self.assertIn(expected_message, str(context.exception))
        self.assertEqual(
            self.mock_cloud_api.get_package_metadata_for_device.call_count,
            max_attempts,
        )


if __name__ == "__main__":
    unittest.main()
