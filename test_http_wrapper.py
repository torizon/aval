import unittest
from unittest.mock import patch
import requests
from http_wrapper import endpoint_call


class TestEndpointCall(unittest.TestCase):
    @patch("http_wrapper.requests.get")
    def test_get_success(self, mock_get):
        # Mock the response for a successful GET request
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"key": "value"}

        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}
        result = endpoint_call(
            url, "get", headers=headers, body=None, json=None
        )

        self.assertEqual(result.json(), {"key": "value"})
        mock_get.assert_called_once_with(url, headers=headers)

    @patch("http_wrapper.requests.post")
    def test_post_success(self, mock_post):
        # Mock the response for a successful POST request
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "success"}

        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}
        body = {"data": "value"}
        result = endpoint_call(
            url, "post", headers=headers, body=body, json=None
        )

        self.assertEqual(result.json(), {"status": "success"})
        mock_post.assert_called_once_with(
            url, headers=headers, data=body, json=None
        )

    @patch("http_wrapper.requests.delete")
    def test_delete_success(self, mock_post):
        # Mock the response for a successful DELETE request
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "success"}

        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}
        result = endpoint_call(
            url, "delete", headers=headers, body=None, json=None
        )

        self.assertEqual(result.json(), {"status": "success"})
        mock_post.assert_called_once_with(url, headers=headers)

    @patch("http_wrapper.requests.get")
    def test_unsupported_request_type(self, mock_get):
        # Simulate a unsupported request type
        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}

        with self.assertRaises(Exception) as context:
            endpoint_call(url, "posr", headers=headers, body=None, json=None)

        self.assertEqual(
            str(context.exception),
            "Unexpected Error: request type posr not supported",
        )
        mock_get.assert_not_called()

    @patch("http_wrapper.requests.get")
    def test_get_http_code_error(self, mock_get):
        # Simulate a connection error
        mock_get.side_effect = requests.exceptions.HTTPError("405")

        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}

        with self.assertRaises(Exception) as context:
            endpoint_call(url, "get", headers=headers, body=None, json=None)

        self.assertEqual(
            str(context.exception),
            "Http Error: 405",
        )
        mock_get.assert_called_once_with(url, headers=headers)

    @patch("http_wrapper.requests.get")
    def test_get_connection_error(self, mock_get):
        # Simulate a connection error
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Failed to connect"
        )

        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}

        with self.assertRaises(Exception) as context:
            endpoint_call(url, "get", headers=headers, body=None, json=None)

        self.assertEqual(
            str(context.exception),
            "Error Connecting: Failed to connect",
        )
        mock_get.assert_called_once_with(url, headers=headers)

    @patch("http_wrapper.requests.get")
    def test_get_timeout_error(self, mock_get):
        # Simulate a timeout error
        mock_get.side_effect = requests.exceptions.Timeout(
            "Connection timed out"
        )

        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}

        with self.assertRaises(Exception) as context:
            endpoint_call(url, "get", headers=headers, body=None, json=None)

        self.assertEqual(
            str(context.exception),
            "Timeout Error: Connection timed out",
        )
        mock_get.assert_called_once_with(url, headers=headers)

    @patch("http_wrapper.requests.get")
    def test_other_request_exception(self, mock_get):
        # Simulate an else HTTP exception
        mock_get.side_effect = requests.exceptions.RequestException(
            "Testing other request exception!"
        )

        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}

        with self.assertRaises(Exception) as context:
            endpoint_call(url, "get", headers=headers, body=None, json=None)

        self.assertEqual(
            str(context.exception),
            "Oops: Something Else: Testing other request exception!",
        )
        mock_get.assert_called_once_with(url, headers=headers)

    @patch("http_wrapper.requests.get")
    def test_unexpected_exception(self, mock_get):
        # Simulate a not known error
        mock_get.side_effect = Exception("Not request error")

        url = "http://example.com/api"
        headers = {"Authorization": "Bearer token"}

        with self.assertRaises(Exception) as context:
            endpoint_call(url, "get", headers=headers, body=None, json=None)

        self.assertEqual(
            str(context.exception), "Unexpected Error: Not request error"
        )
        mock_get.assert_called_once_with(url, headers=headers)
