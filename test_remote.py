import unittest
from unittest.mock import patch, MagicMock
import logging
from remote import Remote

logging.getLogger().setLevel(logging.CRITICAL)


class TestRemote(unittest.TestCase):
    def setUp(self):
        self.mock_dut = MagicMock()
        self.mock_dut.remote_session_ip = "192.168.1.1"
        self.mock_dut.remote_session_port = 22
        self.mock_dut.uuid = "test-uuid"

        self.env_vars = {"USE_RAC": False, "DEVICE_PASSWORD": "password"}

    @patch("remote.Connection", autospec=True)
    def test_test_connection_success_on_first_try(self, MockConnection):
        mock_connection = MockConnection.return_value
        mock_run = mock_connection.run

        # Simulate a successful connection on the first try
        mock_run.return_value.exited = 0

        _ = Remote(dut=self.mock_dut, env_vars=self.env_vars)

        mock_run.assert_called_once_with("true", warn=True, hide=True)
        self.assertEqual(mock_run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
