import unittest
from unittest.mock import patch, MagicMock
import logging
from remote import Remote
from device import Device

logging.getLogger().setLevel(logging.CRITICAL)


class TestRemote(unittest.TestCase):
    @patch("remote.Connection", autospec=True)
    def test_test_connection_success_on_first_try(self, MockConnection):
        mock_device = MagicMock(spec=Device)
        mock_device.remote_session_port = 22
        mock_connection = MockConnection.return_value
        mock_run = mock_connection.run

        # Simulate a successful connection on the first try
        mock_run.return_value.exited = 0

        remote = Remote(
            device=mock_device, address="192.168.1.1", password="password"
        )

        result = remote.test_connection(sleep_time=0)

        self.assertTrue(result)
        mock_run.assert_called_once_with("true", warn=True, hide=True)
        self.assertEqual(mock_run.call_count, 1)

    @patch("remote.Connection", autospec=True)
    def test_test_connection_success_on_fifth_try(self, MockConnection):
        mock_device = MagicMock(spec=Device)
        mock_device.remote_session_port = 22
        mock_connection = MockConnection.return_value
        mock_run = mock_connection.run

        # Simulate exceptions on the first four tries and success on the fifth
        mock_run.side_effect = [
            MagicMock(exited=1),
            Exception("timed out"),
            MagicMock(exited=1),
            Exception("Connection failed"),
            MagicMock(exited=0),
        ]

        remote = Remote(
            device=mock_device, address="192.168.1.1", password="password"
        )

        result = remote.test_connection(sleep_time=0)

        self.assertTrue(result)
        mock_run.assert_any_call("true", warn=True, hide=True)
        self.assertEqual(mock_run.call_count, 5)

    @patch("remote.Connection", autospec=True)
    def test_test_connection_failure(self, MockConnection):
        mock_device = MagicMock(spec=Device)
        mock_device.remote_session_port = 22
        mock_connection = MockConnection.return_value
        mock_run = mock_connection.run

        # Simulate a failed connection
        mock_run.side_effect = Exception("Connection failed")

        remote = Remote(
            device=mock_device, address="192.168.1.1", password="password"
        )

        result = remote.test_connection(sleep_time=0)

        self.assertFalse(result)
        self.assertEqual(mock_run.call_count, 5)

    @patch("remote.Connection.run")
    def test_test_connection_else_case(self, mock_run):
        mock_device = MagicMock(spec=Device)
        mock_result = MagicMock()
        mock_result.exited = 1
        mock_run.return_value = mock_result

        remote = Remote(
            device=mock_device, address="192.168.1.1", password="test-password"
        )

        result = remote.test_connection(sleep_time=0)

        # The function should retry and eventually return False
        self.assertFalse(result)
        self.assertEqual(mock_run.call_count, 5)
