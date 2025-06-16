import requests
from typing import Optional, Dict, Any

def _request(
    method: str,
    url: str,
    headers: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    """
    Internal helper to make an HTTP request with uniform error handling.
    Prints the error detail only for POST requests, then raises a new HTTPError
    with status code and detail. Supports JSON, form-encoded data, or multipart files.
    """
    response = requests.request(
        method,
        url,
        headers=headers,
        params=params,
        json=json,
        data=data,
        files=files,            # ← pass through multipart uploads
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        # Try to extract a JSON “message” or fall back to raw text
        print('hello world')
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text

        # Only POST prints the detail, just like the original
        if method.upper() == "POST":
            print(f"detail {detail}")
        print(f"response.status_code {response.status_code}")

        # Re-raise with more context
        raise requests.exceptions.HTTPError(
            f"HTTP {response.status_code} Error for {url!r}: {detail!r}",
            response=response
        )
    return response

def requestPost(
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    formbody: Optional[Dict[str, Any]] = None,
    files:   Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None
) -> requests.Response:
    """
    Sends a POST request.
      - If `files` is provided, does a multipart/form-data upload.
      - Elif `formbody` is provided, sends application/x-www-form-urlencoded.
      - Else, sends JSON (`payload`).
    """
    if files is not None:
        # multipart/form-data; requests will set Content-Type and boundary
        return _request(
            "POST",
            url,
            headers=headers,
            files=files
        )

    # fall back to form-encoded vs JSON
    return _request(
        "POST",
        url,
        headers=headers,
        data=formbody,
        json=None if formbody is not None else payload
    )


def requestGet(
    url: str,
    headers: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None
) -> requests.Response:
    return _request("GET", url, headers=headers, params=params)

def requestPatch(
    url: str,
    headers: Dict[str, Any],
    body: Dict[str, Any]
) -> requests.Response:
    return _request("PATCH", url, headers=headers, json=body)

def requestPut(
    url: str,
    headers: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None
) -> requests.Response:
    return _request("PUT", url, headers=headers, json=data)
