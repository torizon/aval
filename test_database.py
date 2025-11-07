import os
import unittest
from unittest.mock import patch, MagicMock, call
import threading
import time

os.environ["POSTGRES_DB"] = "test_db"
os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_password"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"

# E402 requires imports to be on top of the file, but we must export the
# POSTGRES* environment variables before `import`ing `database`, so we
# ignore the linter in this case.
import database  # noqa: E402


class TestDatabase(unittest.TestCase):
    @patch("database.acquire_lock")
    def test_try_until_locked_success(self, mock_acquire_lock):
        mock_acquire_lock.return_value = True
        result = database.try_until_locked(
            "5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE"
        )
        self.assertTrue(result)

        mock_acquire_lock.assert_called_once_with(
            "5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE"
        )

    @patch("database.acquire_lock")
    @patch("database.time.sleep")
    @patch("database.logger")
    def test_try_until_locked_failure(
        self, mock_logger, mock_sleep, mock_acquire_lock
    ):
        mock_acquire_lock.return_value = False
        device_uuid = "5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE"

        with self.assertRaises(Exception) as context:
            database.try_until_locked(
                device_uuid, max_attempts=3, sleep=0.1, fail_fast=False
            )

        self.assertEqual(
            str(context.exception),
            "Wasn't able to lock the device 5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE after 3 attempts. :(",
        )

        self.assertEqual(mock_acquire_lock.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 3)

        mock_acquire_lock.assert_called_with(device_uuid)
        mock_sleep.assert_called_with(0.1)

    @patch("database.get_db_connection")
    def test_heartbeat_worker_updates_and_stops(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        stop_event = threading.Event()

        t = threading.Thread(
            target=database._heartbeat_worker,
            args=("5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE", stop_event, 0.1),
            daemon=True,
        )
        t.start()
        time.sleep(0.25)
        stop_event.set()
        t.join(timeout=5)

        # ensures that the UPDATE was called at least once
        self.assertTrue(mock_cursor.execute.called)
        calls = mock_cursor.execute.call_args_list
        self.assertIn(
            call(
                "UPDATE devices SET timestamp = NOW() WHERE device_uuid = %s",
                ("5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE",),
            ),
            calls,
        )

    @patch("database.get_db_connection")
    def test_acquire_lock_starts_heartbeat_thread(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = (False,)

        result = database.acquire_lock("5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE")
        self.assertTrue(result)

        self.assertIsNotNone(database._heartbeat_thread)
        self.assertTrue(database._heartbeat_thread.is_alive())

        database._heartbeat_stop_event.set()
        database._heartbeat_thread.join(timeout=2)
        database._heartbeat_thread = None
        database._heartbeat_stop_event = None

    @patch("database.get_db_connection")
    def test_release_lock_stops_heartbeat_thread(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        database._heartbeat_stop_event = threading.Event()
        database._heartbeat_thread = threading.Thread(
            target=lambda: time.sleep(1), daemon=True
        )
        database._heartbeat_thread.start()

        database.release_lock("5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE")

        mock_cursor.execute.assert_called_with(
            "UPDATE devices SET is_locked = FALSE WHERE device_uuid = %s",
            ("5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE",),
        )

        self.assertIsNone(database._heartbeat_thread)
        self.assertIsNone(database._heartbeat_stop_event)


if __name__ == "__main__":
    unittest.main()
