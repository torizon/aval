import unittest
from unittest.mock import MagicMock, patch

from device_matcher import find_possible_devices


class TestDeviceMatcher(unittest.TestCase):
    def setUp(self):
        patcher = patch("device_matcher.logging")
        self.addCleanup(patcher.stop)
        self.mock_logging = patcher.start()
        self.logger = MagicMock()
        self.mock_logging.getLogger.return_value = self.logger

        patcher_sys_exit = patch("device_matcher.sys.exit")
        self.addCleanup(patcher_sys_exit.stop)
        self.mock_sys_exit = patcher_sys_exit.start()

        self.sample_devices = [
            {
                "deviceUuid": "uuid1",
                "deviceId": "verdin-imx8mm-07214001-9334fa",
                "notes": "0001",
            },
            {
                "deviceUuid": "uuid2",
                "deviceId": "verdin-imx8mp-15247251-0bd6e5",
                "notes": "0002",
            },
            {
                "deviceUuid": "uuid3",
                "deviceId": "verdin-am62-15133530-24fe44",
                "notes": "0003",
            },
            {
                "deviceUuid": "uuid4",
                "deviceId": "colibri-imx7-emmc-15149329-6f39ce",
                "notes": "",  # Device with no PID4
            },
            {
                "deviceUuid": "uuid5",
                "deviceId": "colibri-imx7-emmc-15149329-6f39ce",
                "notes": "asdf",  # Device with invalid PID4
            },
        ]

        self.cloud = MagicMock()
        self.cloud.provisioned_devices = self.sample_devices

        self.args = MagicMock()
        self.args.device_config = None

        self.env_vars = {
            "TEST_WHOLE_FLEET": False,
            "TARGET_BUILD_TYPE": "some_build_type",
            "SOC_UDT": "some_soc_udt",
        }

    @patch("device_matcher.convolute")
    @patch("device_matcher.common")
    def test_find_possible_devices_whole_fleet(
        self, mock_common, mock_convolute
    ):
        self.env_vars["TEST_WHOLE_FLEET"] = True

        possible_duts = find_possible_devices(
            self.cloud, self.args, self.env_vars
        )

        self.assertEqual(possible_duts, self.sample_devices)

        self.logger.info.assert_any_call(
            "Finding possible devices to send tests to..."
        )
        self.logger.info.assert_any_call(
            "Found these devices to send tests to:"
        )
        mock_common.pretty_print_devices.assert_called_with(self.sample_devices)

    @patch("device_matcher.convolute")
    @patch("device_matcher.common")
    def test_find_possible_devices_filtered_devices(
        self, mock_common, mock_convolute
    ):
        pid4_map = {
            "some_soc_udt": ["0001", "0002"],
        }

        mock_convolute.load_pid_map.return_value = pid4_map
        mock_convolute.get_pid4_list.return_value = ["0001", "0002"]

        possible_duts = find_possible_devices(
            self.cloud, self.args, self.env_vars
        )

        expected_devices = [
            {
                "deviceUuid": "uuid1",
                "deviceId": "verdin-imx8mm-07214001-9334fa",
                "notes": "0001",
            },
            {
                "deviceUuid": "uuid2",
                "deviceId": "verdin-imx8mp-15247251-0bd6e5",
                "notes": "0002",
            },
        ]
        self.assertEqual(possible_duts, expected_devices)

        self.logger.error.assert_any_call(
            f"The following device has an invalid PID4 'asdf' in the `notes` field: {self.sample_devices[-1]}"
        )

    @patch("device_matcher.convolute")
    @patch("device_matcher.common")
    def test_find_possible_devices_no_matching_devices(
        self, mock_common, mock_convolute
    ):
        pid4_map = {
            "some_soc_udt": [],
        }

        mock_convolute.load_pid_map.return_value = pid4_map
        mock_convolute.get_pid4_list.return_value = []

        possible_duts = find_possible_devices(
            self.cloud, self.args, self.env_vars
        )
        # Since no devices match the config data, it should be empty
        self.assertEqual(possible_duts, [])

        self.logger.error.assert_called_with(
            "Couldn't find any possible devices to send tests to"
        )

    @patch("device_matcher.convolute")
    @patch("device_matcher.common")
    def test_find_possible_devices_device_with_no_pid4(
        self, mock_common, mock_convolute
    ):
        pid4_map = {
            "some_soc_udt": ["0001", "0002", "0003", ""],
        }

        mock_convolute.load_pid_map.return_value = pid4_map
        mock_convolute.get_pid4_list.return_value = ["0001", "0002", "0003", ""]

        possible_duts = find_possible_devices(
            self.cloud, self.args, self.env_vars
        )

        expected_devices = [
            {
                "deviceUuid": "uuid1",
                "deviceId": "verdin-imx8mm-07214001-9334fa",
                "notes": "0001",
            },
            {
                "deviceUuid": "uuid2",
                "deviceId": "verdin-imx8mp-15247251-0bd6e5",
                "notes": "0002",
            },
            {
                "deviceUuid": "uuid3",
                "deviceId": "verdin-am62-15133530-24fe44",
                "notes": "0003",
            },
        ]
        self.assertEqual(possible_duts, expected_devices)

        self.logger.error.assert_any_call(
            f"The following device has no PID4 set in the `notes` field: {self.sample_devices[3]}"
        )

    @patch("device_matcher.convolute")
    @patch("device_matcher.common")
    def test_find_possible_devices_missing_pid4_in_device_config(
        self, mock_common, mock_convolute
    ):
        device_config_data = ("some_soc_udt", {"property1": "value1"})
        mock_convolute.get_device_config_data.return_value = device_config_data

        pid4_map = {
            "some_soc_udt": [],
        }
        mock_convolute.load_pid_map.return_value = pid4_map
        mock_convolute.get_pid4_list_with_device_config.return_value = []

        possible_duts = find_possible_devices(
            self.cloud, self.args, self.env_vars
        )
        # Since no devices match the config data, it should be empty
        self.assertEqual(possible_duts, [])

        self.logger.error.assert_called_with(
            "Couldn't find any possible devices to send tests to"
        )

    @patch("device_matcher.convolute")
    @patch("device_matcher.common")
    def test_pid4_must_contain_exactly_4_digits(
        self, mock_common, mock_convolute
    ):
        pid4_map = {
            "some_soc_udt": ["asdf"],
        }

        mock_convolute.load_pid_map.return_value = pid4_map
        mock_convolute.get_pid4_list.return_value = ["asdf"]

        possible_duts = find_possible_devices(
            self.cloud, self.args, self.env_vars
        )

        # Since 'asdf' is invalid, no devices should match
        self.assertEqual(possible_duts, [])

        self.logger.error.assert_any_call(
            f"The following device has an invalid PID4 'asdf' in the `notes` field: {self.sample_devices[-1]}"
        )


if __name__ == "__main__":
    unittest.main()
