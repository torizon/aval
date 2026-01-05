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
        elif request_type == "head":
            res = requests.head(url, headers=headers)
        elif request_type == "post":
            res = requests.post(url, headers=headers, data=body, json=json_data)
        elif request_type == "delete":
            res = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"request type {request_type} not supported")

        res.raise_for_status()
        return res

    except requests.exceptions.RequestException as e:
        if e.response is not None:
            try:
                logger.error(json.dumps(e.response.json(), indent=2))
            except Exception:
                logger.error(e.response.text)
        logger.error(f"Request failed: {e}")
        raise
