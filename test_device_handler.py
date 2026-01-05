import unittest
from unittest.mock import MagicMock, patch, call
import sys
import subprocess

from device_handler import process_devices


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
        self.devices = [self.device]
        self.cloud = MagicMock()
        self.env_vars = {
            "PUBLIC_KEY": "public_key_content",
            "DEVICE_PASSWORD": "device_password",
            "TARGET_BUILD_TYPE": "some_build_type",
            "USE_RAC": False,
        }
        self.args = MagicMock()

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("subprocess.check_call")
    def test_process_device_with_command_posix(
        self, mock_check_call, mock_Device, mock_common, mock_database
    ):
        _ = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.network_info = {"ip": "192.168.1.100"}
        dut_instance.test_connection.return_value = True
        dut_instance.connection = MagicMock()

        mock_Device.return_value = dut_instance

        args = MagicMock()
        args.command = 'echo "Hello World"'
        args.before = None
        args.copy_artifact = None
        args.run_before_on_host = 'echo "Running pre-command on host"'

        with patch("os.name", "posix"):
            result = process_devices(
                self.devices, self.cloud, self.env_vars, args
            )

        self.assertTrue(result)
        mock_check_call.assert_called_once_with(
            args.run_before_on_host,
            shell=True,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
        )
        dut_instance.connection.run.assert_called_once_with(args.command)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("subprocess.check_call")
    def test_process_device_with_command_windows(
        self, mock_check_call, mock_Device, mock_common, mock_database
    ):
        _ = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.network_info = {"ip": "192.168.1.100"}
        dut_instance.test_connection.return_value = True
        dut_instance.connection = MagicMock()

        mock_Device.return_value = dut_instance

        args = MagicMock()
        args.command = 'Write-Output "Hello World"'
        args.before = None
        args.copy_artifact = None
        args.run_before_on_host = 'Write-Output "Running pre-command on host"'

        with patch("os.name", "nt"):
            result = process_devices(
                self.devices, self.cloud, self.env_vars, args
            )

        self.assertTrue(result)
        mock_check_call.assert_called_once_with(
            ["powershell", "-Command", args.run_before_on_host],
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
        )
        dut_instance.connection.run.assert_called_once_with(args.command)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_process_device_with_command_unknown_os(
        self, mock_Device, mock_common, mock_database
    ):
        _ = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.network_info = {"ip": "192.168.1.100"}
        dut_instance.test_connection.return_value = True
        dut_instance.connection = MagicMock()

        mock_Device.return_value = dut_instance

        args = MagicMock()
        args.command = "unknown_command"
        args.before = None
        args.copy_artifact = None
        args.run_before_on_host = "unknown_command"

        with patch("os.name", "unknown_os"):
            process_devices(self.devices, self.cloud, self.env_vars, args)

        self.logger.error.assert_called_with(
            f"An error occurred while processing device {_}: Unsupported unknown_os OS"
        )

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_process_device_successful(
        self, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = False
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.test_connection.return_value = True
        mock_Device.return_value = dut_instance

        result = process_devices(
            self.devices, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        mock_database.device_exists.assert_called_with(uuid)
        mock_database.create_device.assert_called_with(uuid)
        self.logger.info.assert_any_call(f"Lock acquired for device {uuid}")

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_process_device_failed_connection(
        self, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = False
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.create_ssh_connnection.side_effect = ConnectionError(
            "Connection test failed"
        )
        mock_Device.return_value = dut_instance

        args = MagicMock()
        args.run_before_on_host = None  # Critical fix
        args.before = None
        args.command = None
        args.copy_artifact = None

        _ = process_devices(self.devices, self.cloud, self.env_vars, args)

        self.mock_sys_exit.assert_called_once_with(1)
        self.logger.error.assert_called_with(
            f"An error occurred while processing device {uuid}: Connection test failed"
        )
        mock_database.release_lock.assert_called_with(uuid)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_process_device_exception_handling(
        self, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        mock_Device.side_effect = Exception("Device initialization failed")

        process_devices(self.devices, self.cloud, self.env_vars, self.args)

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
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = False

        result = process_devices(
            self.devices, self.cloud, self.env_vars, self.args
        )

        self.assertFalse(result)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    @patch("subprocess.check_call")
    def test_process_device_with_copy_artifact(
        self, mock_check_call, mock_Device, mock_common, mock_database
    ):
        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.network_info = {"ip": "192.168.1.100"}
        dut_instance.test_connection.return_value = True
        dut_instance.connection.get = MagicMock()

        mock_Device.return_value = dut_instance
        mock_common.parse_hardware_id.return_value = "verdin-imx8mm"

        args = MagicMock()
        args.copy_artifact = [
            "/remote/path1",
            "/local/output1",
            "/remote/path2",
            "/local/output2",
        ]

        result = process_devices(self.devices, self.cloud, self.env_vars, args)

        dut_instance.connection.get.assert_has_calls(
            [
                call("/remote/path1", "/local/output1"),
                call("/remote/path2", "/local/output2"),
            ],
            any_order=True,
        )
        self.assertTrue(result)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_process_device_use_rac(
        self, mock_Device, mock_common, mock_database
    ):
        self.env_vars["USE_RAC"] = True

        _ = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        mock_Device.return_value = dut_instance
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22

        remote_instance = MagicMock()
        mock_Device.return_value = remote_instance
        remote_instance.test_connection.return_value = True

        result = process_devices(
            self.devices, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        # dut_instance.setup_rac_session.assert_called_with("ras.torizon.io")
        dut_instance.setup_usual_ssh_session.assert_not_called()

    @patch("device_handler.Device")
    @patch("device_handler.database")
    @patch("device_handler.common")
    def test_process_device_device_not_in_database(
        self, mock_common, mock_database, mock_Device
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = False
        mock_database.try_until_locked.return_value = True

        mock_dut = MagicMock()
        mock_dut.is_os_updated_to_latest.return_value = True
        mock_Device.return_value = mock_dut

        result = process_devices(
            self.devices, self.cloud, self.env_vars, self.args
        )

        self.assertTrue(result)
        mock_database.create_device.assert_called_once_with(uuid)
        self.logger.info.assert_any_call(f"Created new device entry for {uuid}")
        self.logger.info.assert_any_call(f"Lock acquired for device {uuid}")
        mock_database.release_lock.assert_called_once_with(uuid)

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_hacking_session_normal_exit(
        self, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.network_info = {"ip": "192.168.1.100"}
        dut_instance.test_connection.return_value = True

        dut_instance.connection = MagicMock()
        dut_instance.connection.shell.return_value = True

        mock_Device.return_value = dut_instance

        args = MagicMock()
        args.command = 'echo "Hello World"'
        args.before = None
        args.copy_artifact = None
        args.hacking_session = True
        args.run_before_on_host = None

        result = process_devices(self.devices, self.cloud, self.env_vars, args)

        self.assertTrue(result)

        self.logger.info.assert_any_call(
            f"Interactive session finished for device {uuid}"
        )
        self.logger.error.assert_not_called()

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_hacking_session_exit_code_1(
        self, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.network_info = {"ip": "192.168.1.100"}
        dut_instance.test_connection.return_value = True

        dut_instance.connection = MagicMock()
        dut_instance.connection.shell.side_effect = Exception("Exit code: 1")

        mock_Device.return_value = dut_instance

        args = MagicMock()
        args.command = 'echo "Hello World"'
        args.before = None
        args.copy_artifact = None
        args.hacking_session = True
        args.run_before_on_host = None

        result = process_devices(self.devices, self.cloud, self.env_vars, args)

        self.assertTrue(result)

        self.logger.info.assert_any_call(
            f"Interactive shell closed normally (exit 1) for device {uuid}"
        )
        self.logger.error.assert_not_called()

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_hacking_session_exit_code_130(
        self, mock_Device, mock_common, mock_database
    ):
        uuid = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.network_info = {"ip": "192.168.1.100"}
        dut_instance.test_connection.return_value = True

        dut_instance.connection = MagicMock()
        dut_instance.connection.shell.side_effect = Exception("Exit code: 130")

        mock_Device.return_value = dut_instance

        args = MagicMock()
        args.command = 'echo "Hello World"'
        args.before = None
        args.copy_artifact = None
        args.hacking_session = True
        args.run_before_on_host = None

        result = process_devices(self.devices, self.cloud, self.env_vars, args)

        self.assertTrue(result)

        self.logger.info.assert_any_call(
            f"Interactive shell closed using SIGINT (exit 130) for device {uuid}"
        )
        self.logger.error.assert_not_called()

    @patch("device_handler.database")
    @patch("device_handler.common")
    @patch("device_handler.Device")
    def test_hacking_session_unexpected_error(
        self, mock_Device, mock_common, mock_database
    ):
        _ = self.device["deviceUuid"]
        hardware_id = "verdin-imx8mm"
        mock_common.parse_hardware_id.return_value = hardware_id

        mock_database.device_exists.return_value = True
        mock_database.try_until_locked.return_value = True

        dut_instance = MagicMock()
        dut_instance.remote_session_ip = "192.168.1.100"
        dut_instance.remote_session_port = 22
        dut_instance.network_info = {"ip": "192.168.1.100"}
        dut_instance.test_connection.return_value = True

        dut_instance.connection = MagicMock()
        dut_instance.connection.shell.side_effect = Exception(
            "Some unexpected error"
        )

        mock_Device.return_value = dut_instance

        args = MagicMock()
        args.command = 'echo "Hello World"'
        args.before = None
        args.copy_artifact = None
        args.hacking_session = True
        args.run_before_on_host = None

        result = process_devices(self.devices, self.cloud, self.env_vars, args)

        self.assertTrue(result)

        self.logger.error.assert_any_call(
            "Failed to start interactive shell: Some unexpected error"
        )


if __name__ == "__main__":
    unittest.main()
