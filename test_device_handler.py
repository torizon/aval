import unittest
from unittest.mock import MagicMock, patch, call
import sys

from device_handler import process_device


class TestDeviceHandler(unittest.TestCase):
    def setUp(self):
        patcher_logging = patch("device_handler.logging")
        self.addCleanup(patcher_logging.stop)
        self.mock_logging = patcher_logging.start()
        self.logger = MagicMock()
        self.mock_logging.getLogger.return_value = self.logger

        patcher_sys_exit = patch("device_handler.sys.exit")
        self.addCleanup(patcher_sys_exit.stop)
        self.mock_sys_exit = patcher_sys_exit.start()

        self.device = {
            "deviceUuid": "uuid1",
            "deviceId": "verdin-imx8mm-07214001-9334fa",
            "notes": "pid4_1",
        }
        self.cloud = MagicMock()
        self.env_vars = {
            "PUBLIC_KEY": "public_key_content",
            "DEVICE_PASSWORD": "device_password",
            "TARGET_BUILD_TYPE": "some_build_type",
            "USE_RAC": False,
        }
        self.args = MagicMock()
        self.args.before = None
        self.args.command = 'echo "Hello World"'
        self.args.copy_artifact = None

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("device_handler.Remote")
    def test_process_device_successful(
        self, mock_Remote, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = False
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        mock_Device.return_value = dut_instance
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22

        remote_instance = MagicMock()
        mock_Remote.return_value = remote_instance
        remote_instance.test_connection.return_value = True

        result = process_device(
            self.device, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        mock_database.device_exists.assert_called_with(uuid)
        mock_database.create_device.assert_called_with(uuid)
        mock_database.try_until_locked.assert_called_with(uuid)
        self.logger.info.assert_any_call(f"Lock acquired for device {uuid}")
        self.logger.debug.assert_any_call(
            f"Connection test succeeded for device {uuid}"
        )
        self.logger.info.assert_any_call(
            f"Command '{self.args.command}' executed for device {uuid}"
        )
        self.logger.info.assert_any_call(f"Lock released for device {uuid}")
        mock_database.release_lock.assert_called_with(uuid)
        remote_instance.connection.run.assert_called_with(self.args.command)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("device_handler.Remote")
    def test_process_device_failed_connection(
        self, mock_Remote, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        mock_Device.return_value = dut_instance
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22

        remote_instance = MagicMock()
        mock_Remote.return_value = remote_instance
        remote_instance.test_connection.return_value = False

        result = process_device(
            self.device, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        self.logger.error.assert_called_with(
            f"Connection test failed for device {uuid}"
        )
        mock_database.release_lock.assert_called_with(uuid)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("device_handler.Remote")
    def test_process_device_exception_handling(
        self, mock_Remote, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        mock_Device.side_effect = Exception("Device initialization failed")

        process_device(self.device, self.cloud, self.env_vars, self.args)

        self.logger.error.assert_called_with(
            f"An error occurred while processing device {uuid}: Device initialization failed"
        )
        mock_database.release_lock.assert_called_with(uuid)
        self.mock_sys_exit.assert_called_with(1)

    @patch("device_handler.database")
    @patch("device_handler.common")
    def test_process_device_failed_to_acquire_lock(
        self, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = False

        result = process_device(
            self.device, self.cloud, self.env_vars, self.args
        )

        self.assertFalse(result)
        self.logger.info.assert_called_with(
            f"Failed to acquire lock for device {uuid}"
        )

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("device_handler.Remote")
    def test_process_device_with_before_command(
        self, mock_Remote, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        self.args.before = 'echo "Before Command"'

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        mock_Device.return_value = dut_instance
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22

        remote_instance = MagicMock()
        mock_Remote.return_value = remote_instance
        remote_instance.test_connection.return_value = True

        result = process_device(
            self.device, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        calls = [call(self.args.before), call(self.args.command)]
        remote_instance.connection.run.assert_has_calls(calls)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("device_handler.Remote")
    def test_process_device_with_copy_artifact(
        self, mock_Remote, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        self.args.copy_artifact = [
            "/remote/path1",
            "/local/output1",
            "/remote/path2",
            "/local/output2",
        ]

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        mock_Device.return_value = dut_instance
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22

        remote_instance = MagicMock()
        mock_Remote.return_value = remote_instance
        remote_instance.test_connection.return_value = True

        result = process_device(
            self.device, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        calls = [
            call("/remote/path1", "/local/output1"),
            call("/remote/path2", "/local/output2"),
        ]
        remote_instance.connection.get.assert_has_calls(calls)
        self.logger.info.assert_any_call(
            f"Artifact retrieved for device {uuid}"
        )

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("device_handler.Remote")
    def test_process_device_use_rac(
        self, mock_Remote, mock_Device, mock_common, mock_database
    ):
        self.env_vars["USE_RAC"] = True

        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        mock_Device.return_value = dut_instance
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22

        remote_instance = MagicMock()
        mock_Remote.return_value = remote_instance
        remote_instance.test_connection.return_value = True

        result = process_device(
            self.device, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        dut_instance.setup_rac_session.assert_called_with("ras.torizon.io")
        dut_instance.setup_usual_ssh_session.assert_not_called()

    @patch("device_handler.database")
    @patch("device_handler.common")
    def test_process_device_device_not_in_database(
        self, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = False

        result = process_device(
            self.device, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        mock_database.create_device.assert_called_with(uuid)
        self.logger.info.assert_any_call(f"Created new device entry for {uuid}")
        self.logger.info.assert_any_call(f"Lock acquired for device {uuid}")


if __name__ == "__main__":
    unittest.main()
