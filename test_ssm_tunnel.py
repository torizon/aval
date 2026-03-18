import importlib
import os
import unittest
from unittest.mock import MagicMock, patch

with patch("logging_setup.setup_logging", return_value=MagicMock()):
    from aws_database import ssm_tunnel


class TestSsmTunnel(unittest.TestCase):
    def setUp(self):
        with patch("logging_setup.setup_logging", return_value=MagicMock()):
            importlib.reload(ssm_tunnel)
        patcher_logger = patch(
            "aws_database.ssm_tunnel.logger", new=MagicMock()
        )
        self.addCleanup(patcher_logger.stop)
        self.logger = patcher_logger.start()

    @patch.dict(os.environ, {"AWS_RDS_HOST": "example-rds-host"}, clear=False)
    @patch("aws_database.ssm_tunnel.atexit.register")
    @patch("aws_database.ssm_tunnel.subprocess.run")
    @patch("aws_database.ssm_tunnel.os.name", "posix")
    def test_ensure_ssm_tunnel_runs_shell_script_once(
        self, mock_run, mock_register
    ):
        ssm_tunnel.ensure_ssm_tunnel()
        ssm_tunnel.ensure_ssm_tunnel()

        mock_run.assert_called_once_with(
            ["sh", unittest.mock.ANY],
            check=True,
        )
        self.assertTrue(
            mock_run.call_args.args[0][1].endswith(
                "aws_database/rds-ssm-tunnel.sh"
            )
        )
        mock_register.assert_called_once_with(ssm_tunnel.close_ssm_tunnel)

    @patch.dict(os.environ, {"AWS_RDS_HOST": "example-rds-host"}, clear=False)
    @patch("aws_database.ssm_tunnel.subprocess.run")
    @patch("aws_database.ssm_tunnel.shutil.which", return_value="powershell")
    @patch("aws_database.ssm_tunnel.os.name", "nt")
    def test_close_ssm_tunnel_runs_powershell_script(
        self, mock_which, mock_run
    ):
        ssm_tunnel._tunnel_started = True

        ssm_tunnel.close_ssm_tunnel()

        self.assertEqual(
            mock_run.call_args.args[0][:5],
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
            ],
        )
        self.assertTrue(
            mock_run.call_args.args[0][5].endswith(
                "aws_database/kill-ssm-tunnels.ps1"
            )
        )
        mock_run.assert_called_once_with(unittest.mock.ANY, check=True)
        mock_which.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("aws_database.ssm_tunnel.subprocess.run")
    def test_ensure_ssm_tunnel_noops_without_aws(self, mock_run):
        ssm_tunnel.ensure_ssm_tunnel()

        mock_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
