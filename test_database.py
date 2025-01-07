import os
import unittest
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
