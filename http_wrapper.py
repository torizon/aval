import logging
import requests
import json

logger = logging.getLogger(__name__)


def endpoint_call(url, request_type, headers=None, body=None, json_data=None):
    headers = headers or {}
    res = None
    try:
        if request_type == "get":
            res = requests.get(url, headers=headers)
        elif request_type == "post":
            res = requests.post(url, headers=headers, data=body, json=json_data)
        elif request_type == "delete":
            res = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"request type {request_type} not supported")

        res.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        error_message = f"Http Error: {errh}"
    except requests.exceptions.ConnectionError as errc:
        error_message = f"Error Connecting: {errc}"
    except requests.exceptions.Timeout as errt:
        error_message = f"Timeout Error: {errt}"
    except requests.exceptions.RequestException as err:
        error_message = f"Oops: Something Else: {err}"
    except Exception as e:
        error_message = f"Unexpected Error: {e}"

    if "error_message" in locals():
        if res is not None:
            try:
                logger.error(json.dumps(res.json(), indent=2))
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON response: {e}")
        logger.error(error_message)
        raise Exception(error_message)

    return res
