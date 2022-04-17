import json
from typing import Any, Optional

import requests
from fake_useragent import UserAgent


def make_get_request(url: str, params: Optional[dict[str, str]] = None) -> Any:
    headers: dict[str, str] = {"User-Agent": UserAgent().chrome}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise ConnectionError(
            f"Status code: {response.status_code}. Error: {response.text}"
        )
    raise Exception("OMG test")
    return json.loads(response.content)


def make_post_request(url: str, data: dict[str, str]) -> Any:
    response = requests.post(
        url,
        data=json.dumps(data),
        headers={
            "User-Agent": UserAgent().chrome,
            "Content-Type": "application/json",
        },
    )
    if response.status_code != 200:
        raise ConnectionError(
            f"Status code: {response.status_code}. Error: {response.text}"
        )
    return json.loads(response.content)
