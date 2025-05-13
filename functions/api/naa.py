import os
import json
from dotenv import load_dotenv
from functions.helpers.constants import loginNAAPostUrl, getNAACasesUrl
from functions.helpers.helpers import requestGet, requestPost, requestPatch,requestPut
from functools import wraps
from requests.exceptions import HTTPError

load_dotenv()
loginNAAEmail = os.getenv("NAA_EMAIL")
loginNAAPassword = os.getenv("NAA_PASSWORD")

# path for storing/reading the token
_CRED_PATH = "credentials/naa_credentials.json"

def load_token(path: str = _CRED_PATH) -> str:
    try:
        with open(path, "r") as f:
            return json.load(f).get("token")
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_token(token: str, path: str = _CRED_PATH):
    with open(path, "w") as f:
        json.dump({"token": token}, f)

# login to NAA — returns raw token string
def loginNAA() -> str:
    payload = {"email": loginNAAEmail, "password": loginNAAPassword}
    response = requestPost(url=loginNAAPostUrl, payload=payload)
    return response.json()['token']

# on import, try to load existing token, otherwise fetch + persist
token = load_token()
if not token:
    token = loginNAA()
    save_token(token)

def reInit():
    global token
    token = loginNAA()
    save_token(token)

# decorator to auto-refresh on 401 Unauthorized
def ensure_authorized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as e:
            # try to parse JSON body
            try:
                err = e.response.json()
            except Exception:
                return {'error': str(e)}
            if err.get("title") == "Unauthorized":
                # refresh token and retry once
                reInit()
                return func(*args, **kwargs)
            # otherwise re-raise
            return {'error': str(e)}
        
    return wrapper

@ensure_authorized
def getNAACases(pageIndex: int = None, pageSize: int = None) -> dict:
    pageIndex = 1 if pageIndex is None else pageIndex
    pageSize = 25 if pageSize is None else pageSize

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "Pager.PageIndex": pageIndex,
        "Pager.PageSize": pageSize,
    }

    response = requestGet(url=getNAACasesUrl, headers=headers, params=params)
    return response.json()

@ensure_authorized
def getCaseByID(caseID: int) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{getNAACasesUrl}/{caseID}"
    print(url)
    response = requestGet(url=url, headers=headers)
    return response.json()

@ensure_authorized
def closeCase(caseID: int) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{getNAACasesUrl}/{caseID}/cancel"
    response = requestPut(url=url, headers=headers)
    return 'success in closeCase for caseID: '+str(caseID)

@ensure_authorized
def postCase(
        outCourtState: str,
        outCourtCounty: str,
        outCourtCity: str,
        outCourtName: str,
        outCourtAddress: str,
        outCourtZip: str,
        hearingType: str,
        hearingDate: str,
        fileNumber: str,
        defendantPlantiff: bool,
        detailedInstructions: str,
        attorneyRecord: str
    ) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    body = {
        "outCourtState": outCourtState,
        "outCourtCounty": outCourtCounty,
        "outCourtCity": outCourtCity,
        "outCourtName": outCourtName,
        "outCourtAddress": outCourtAddress,
        "outCourtZip": outCourtZip,
        "hearingType": hearingType,
        "hearingDate": hearingDate,
        "fileNumber": fileNumber,
        "defendantPlantiff": defendantPlantiff,
        "detailedInstructions": detailedInstructions,
        "attorneyRecord": attorneyRecord
    }
    url = getNAACasesUrl
    response = requestPost(url=url, headers=headers, payload=body)
    return response.json()  # Return the response only if successful

