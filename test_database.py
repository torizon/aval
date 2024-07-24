import unittest
from unittest.mock import patch
import database


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
    def test_try_until_locked_failure(self, mock_acquire_lock):
        mock_acquire_lock.return_value = False

        with self.assertRaises(Exception) as context:
            database.try_until_locked(
                "5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE", interval=3, sleep=0.1
            )

        self.assertEqual(
            str(context.exception),
            "Wasn't able to lock the device 5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE in time. :(",
        )

        self.assertEqual(mock_acquire_lock.call_count, 3)

        mock_acquire_lock.assert_called_with(
            "5B76B5C7-FCCD-4FCD-A100-0CE33E8DCDFE"
        )
