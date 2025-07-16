import os
from dotenv import load_dotenv
from functions.helpers.helpers import requestGet, requestPut
from functions.api.generate_zoho_auth import zoho_generate_authtoken
import json
from functools import wraps
from requests.exceptions import HTTPError
from typing import Any, Dict
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
            except ZohoApiError as zerr:
                return {'error': str(zerr), 'statusCode':zerr['statusCode']}
            except Exception:
                return {'error': str(e), 'statusCode':e.response['statusCode']}
            if "invalid oauth token" in err.get("message"):
                # refresh token and retry once
                reInit()
                return func(*args, **kwargs)
            # otherwise re-raise
            return {'error': str(e),'statusCode': e.response['statusCode']}
        
    return wrapper

def initConfig(path: str = "credentials/credentials.json") -> dict:
    with open(path, "r") as f:
        return json.load(f)

    
load_dotenv(override=True)
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET= os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REDEIRECT_URI = os.getenv("ZOHO_REDIRECT_URI")
ZOHO_SCOPES = os.getenv("ZOHO_SCOPES")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHOCRM_REFRESH_TOKEN")
ZOHO_API_DOMAIN = os.getenv("ZOHO_API_DOMAIN")
ZOHO_TOKEN_TYPE= os.getenv("ZOHO_TOKEN_TYPE")
ZOHO_EXPIRES_IN = os.getenv("ZOHO_EXPIRES_IN")
ZOHOCRM_ACCESS_TOKEN = os.getenv("ZOHOCRM_ACCESS_TOKEN")
ZOHOCRM_EXPIRES_IN = os.getenv("ZOHOCRM_EXPIRES_IN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")


MODULE_API_NAME = 'Appearances1'
baseUrl = f'{ZOHO_API_DOMAIN}/crm/v7/{MODULE_API_NAME}/'
baseUrlMatters = f'{ZOHO_API_DOMAIN}/crm/v8/Deals/search?criteria=(id:equals:'
filesUrl = f'{ZOHO_API_DOMAIN}/crm/v7/files?id='

def reInit():
    global ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REDEIRECT_URI
    global ZOHO_SCOPES, ZOHO_REFRESH_TOKEN, ZOHO_API_DOMAIN
    global ZOHO_TOKEN_TYPE, ZOHO_EXPIRES_IN
    global ZOHOCRM_ACCESS_TOKEN, ZOHOCRM_EXPIRES_IN
    global ACCESS_TOKEN

    zoho_generate_authtoken()
    cred = initConfig()
    ACCESS_TOKEN        = cred['access_token']

class ZohoApiError(HTTPError):
    """Raised when the Zoho API returns an HTTP error response."""
    def __init__(self, message: str, response=None):
        # HTTPError’s constructor signature is (message, response=response)
        super().__init__(message, response=response)

@ensure_authorized
def searchZohoRecords(matterID: int) -> Dict[str, Any]:
    """
    Look up a Zoho record by its ID.

    Raises
    ------
    ZohoApiError
        If the HTTP status is anything other than 200 OK, or if the body
        can’t be parsed as JSON.
    """
    headers = {"Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}"}
    url = f"{baseUrl}search?criteria=id:equals:{matterID}"

    response = requestGet(headers=headers, url=url)

    #––– 1. Enforce exact-200 success –––––––––––––––––––––––––––––––––––
    if response.status_code == 204:
        resString = f"Zoho search failed (HTTP {response.status_code}): empty response from search zohoRecords for matterID {matterID}"
        raise ZohoApiError(
            resString, response={'error':resString,'statusCode': 409}
        )

    #––– 2. Parse JSON safely –––––––––––––––––––––––––––––––––––––––––––
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        # 200 with an empty body (204 scenario) triggers this
        resString = f"Zoho search returned invalid JSON: {exc} — body: {response.text}"
        raise ZohoApiError(
            resString,response = {'error':resString,'statusCode':500}
        ) from exc


@ensure_authorized
def searchZohoContacts(matterID: str) -> Dict[str, Any]:
    """
    Look up a Zoho record by its ID.

    Raises
    ------
    ZohoApiError
        If the HTTP status is anything other than 200 OK, or if the body
        can’t be parsed as JSON.
    """
    headers = {"Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}"}
    url = f"{baseUrlMatters}{matterID})"

    response = requestGet(headers=headers, url=url)

    #––– 1. Enforce exact-200 success –––––––––––––––––––––––––––––––––––
    if response.status_code == 204:
        resString = f"Zoho search failed (HTTP {response.status_code}): empty response from search zoho contacts for {matterID}"
        raise ZohoApiError(
        resString, response={'error':resString,'statusCode': 409}
        )

    #––– 2. Parse JSON safely –––––––––––––––––––––––––––––––––––––––––––
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        # 200 with an empty body (204 scenario) triggers this
        resString = f"Zoho search returned invalid JSON: {exc} — body: {response.text}"
        raise ZohoApiError(
            resString, response={'error':resString,'statusCode':500}
        ) from exc



#add case id to zoho record
@ensure_authorized 
def addCaseIDToZohoRecord(matterID:int,caseID:int) -> dict:
    formatToken = f"Zoho-oauthtoken {ACCESS_TOKEN}"
    headers = {
        "Authorization" :formatToken 
    }
    data = {
        "data":[
            {
                "NAAM_CaseID": caseID,
            }
        ]
    }
    url = f"{baseUrl}{matterID}"
    response = requestPut(headers=headers,url=url,data=data)
    return response.json()

@ensure_authorized
def updateResults(matterID:int,result:str) -> dict:
    formatToken = f"Zoho-oauthtoken {ACCESS_TOKEN}"
    headers = {
        "Authorization" :formatToken 
    }
    data = {
        "data":[
            {
                "NAAM_Results": result,
            }
        ]
    }
    url = f"{baseUrl}{matterID}"
    response = requestPut(headers=headers,url=url,data=data)
    return response.json()


@ensure_authorized
def getListOfSyncIds() -> dict:
    formatToken = f"Zoho-oauthtoken {ACCESS_TOKEN}"

    headers = {
        "Authorization" :formatToken 
    }
    # url = f"{baseUrl}search?criteria=id:equals:{matterID}"
    urlSubmit = f"{baseUrl}search?criteria=Submission_Status:equals:Submitted"

    submittedResponse = requestGet(headers=headers,url=urlSubmit)

    submittedResponses = []
    submittedResponses = [response['id'] for response in submittedResponse.json()['data']] if len(submittedResponse.json()['data']) > 0 else []


    urlDead = f"{baseUrl}search?criteria=Submission_Status:equals:Dead"
    deadResponse = requestGet(headers=headers,url=urlDead)
    deadResponses = []
    deadResponses = [response['id'] for response in deadResponse.json()['data']] if len(deadResponse.json()['data']) > 0 else []

    urlNew = f"{baseUrl}search?criteria=Submission_Status:equals:New"
    newResponse = requestGet(headers=headers,url=urlNew)
    newResponses = []
    newResponses = [response['id'] for response in newResponse.json()['data']] if len(newResponse.json()['data']) > 0 else []



    
    return {'response': submittedResponses + deadResponses + newResponses}


#add case id to zoho record
@ensure_authorized 
def getFileFromZoho(fileId:str) -> dict:
    formatToken = f"Zoho-oauthtoken {ACCESS_TOKEN}"
    headers = {
        "Authorization" :formatToken 
    }
    url = f'{filesUrl}{fileId}'
    response = requestGet(headers=headers,url=url)
    return {'statusCode': response.status_code, 'response': response.content}