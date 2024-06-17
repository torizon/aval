import unittest
from unittest.mock import MagicMock, patch
from remote import Remote


class TestRemote(unittest.TestCase):

    def setUp(self):
        self.mock_device = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_device.remote_session_port = 22

        self.patcher_connection = patch(
            "remote.Connection", return_value=self.mock_connection
        )
        self.patcher_logging = patch("remote.logging.getLogger")

        self.mocked_connection = self.patcher_connection.start()
        self.mocked_logging = self.patcher_logging.start()

    def tearDown(self):
        self.patcher_connection.stop()
        self.patcher_logging.stop()

    def test_successful_connection(self):
        remote_instance = Remote(
            self.mock_device, "dummy_address", "dummy_password"
        )
        self.mock_connection.run.return_value.exited = 0

        result = remote_instance.test_connection()

        self.assertTrue(result)
        self.mocked_logging.return_value.info.assert_called_once_with(
            "Remote connection test OK"
        )
        self.mock_connection.run.assert_called_once_with(
            "true", warn=True, hide=True
        )

    def test_failed_connection_with_retries(self):
        remote_instance = Remote(
            self.mock_device, "dummy_address", "dummy_password"
        )
        self.mock_connection.run.side_effect = Exception("Connection failed")

        result = remote_instance.test_connection()

        self.assertFalse(result)
        self.assertEqual(self.mock_connection.run.call_count, 5)
        self.mocked_logging.return_value.error.assert_called_with(
            "Remote connection test failed"
        )


if __name__ == "__main__":
    unittest.main()
