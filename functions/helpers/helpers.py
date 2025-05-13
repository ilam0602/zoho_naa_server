
import requests

#generic function for post request
def requestPost(url:str, payload:dict,headers:dict = None):
    response = requests.post(url, json=payload,headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # try to extract a JSON “message” or fall back to raw text
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text
        print(f'detail {detail}')

        # build and raise a new, more informative exception
        raise requests.exceptions.HTTPError(
            f"HTTP {response.status_code} Error for {url!r}: {detail!r}",
            response=response
        )
    return response 

#generic function for get request
def requestGet(url:str,headers:dict,params:dict = None):
    response = requests.get(url, headers= headers,params=params)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # try to extract a JSON “message” or fall back to raw text
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text

        # build and raise a new, more informative exception
        raise requests.exceptions.HTTPError(
            f"HTTP {response.status_code} Error for {url!r}: {detail!r}",
            response=response
        )
    return response

#generic function for patch request
def requestPatch(url:str,headers:dict,body:dict):
    response = requests.patch(url, headers= headers,json=body)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # try to extract a JSON “message” or fall back to raw text
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text

        # build and raise a new, more informative exception
        raise requests.exceptions.HTTPError(
            f"HTTP {response.status_code} Error for {url!r}: {detail!r}",
            response=response
        )
    return response

#generic function for put request
def requestPut(url:str,headers:dict,data:dict = None):
    response = requests.put(url, headers= headers,json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # try to extract a JSON “message” or fall back to raw text
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text

        # build and raise a new, more informative exception
        raise requests.exceptions.HTTPError(
            f"HTTP {response.status_code} Error for {url!r}: {detail!r}",
            response=response
        )
    return response