import os
from dotenv import load_dotenv
from functions.helpers.constants import loginNAAPostUrl,getNAACasesUrl
from functions.helpers.helpers import requestGet, requestPost,requestPatch,requestPut
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
            print(f'Error in request {e}')
            # try to parse JSON body
            try:
                err = e.response.json()
                print(f'err {err}')
            except Exception:
                return {'error': str(e)}
            if "invalid oauth token" in err.get("message"):
                # refresh token and retry once
                reInit()
                return func(*args, **kwargs)
            # otherwise re-raise
            return {'error': str(e)}
        
    return wrapper

def initConfig(path: str = "credentials/credentials.json") -> dict:
    with open(path, "r") as f:
        return json.load(f)

    

cred = initConfig()
ZOHO_CLIENT_ID = cred['client_id']
ZOHO_CLIENT_SECRET= cred['client_secret']
ZOHO_REDEIRECT_URI = cred['redirect_uri']
ZOHO_SCOPES = cred['scopes']
ZOHO_REFRESH_TOKEN = cred['refresh_token']
ZOHO_API_DOMAIN = cred['api_domain']
ZOHO_TOKEN_TYPE= cred['token_type']
ZOHO_EXPIRES_IN = cred['expires_in']
ZOHOCRM_ACCESS_TOKEN = cred['zohocrm_access_token']
ZOHOCRM_EXPIRES_IN = cred['zohocrm_expires_in']
ACCESS_TOKEN = cred['access_token']


MODULE_API_NAME = 'Appearances1'
baseUrl = f'{ZOHO_API_DOMAIN}/crm/v7/{MODULE_API_NAME}/'
baseUrlContacts = f'{ZOHO_API_DOMAIN}/crm/v7/Contacts/search?criteria=Account_Name:equals:'
filesUrl = f'{ZOHO_API_DOMAIN}/crm/v7/files?id='

def reInit():
    global ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REDEIRECT_URI
    global ZOHO_SCOPES, ZOHO_REFRESH_TOKEN, ZOHO_API_DOMAIN
    global ZOHO_TOKEN_TYPE, ZOHO_EXPIRES_IN
    global ZOHOCRM_ACCESS_TOKEN, ZOHOCRM_EXPIRES_IN
    global ACCESS_TOKEN

    zoho_generate_authtoken()
    cred = initConfig()
    ZOHO_CLIENT_ID      = cred['client_id']
    ZOHO_CLIENT_SECRET  = cred['client_secret']
    ZOHO_REDEIRECT_URI  = cred['redirect_uri']
    ZOHO_SCOPES         = cred['scopes']
    ZOHO_REFRESH_TOKEN  = cred['refresh_token']
    ZOHO_API_DOMAIN     = cred['api_domain']
    ZOHO_TOKEN_TYPE     = cred['token_type']
    ZOHO_EXPIRES_IN     = cred['expires_in']
    ZOHOCRM_ACCESS_TOKEN= cred['zohocrm_access_token']
    ZOHOCRM_EXPIRES_IN  = cred['zohocrm_expires_in']
    ACCESS_TOKEN        = cred['access_token']

class ZohoApiError(Exception):
    """Raised when the Zoho CRM API returns an unexpected result."""

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
    print(f"url {url}")

    response = requestGet(headers=headers, url=url)
    print(f"response in searchZohoRecords {response}")  # e.g. <Response [204]>
    print(f'response.status_code {response.status_code}')

    #––– 1. Enforce exact-200 success –––––––––––––––––––––––––––––––––––
    if response.status_code == 204:
        raise ZohoApiError(
            f"Zoho search failed (HTTP {response.status_code}): empty response from search zohoRecords for matterID {matterID}"
        )

    #––– 2. Parse JSON safely –––––––––––––––––––––––––––––––––––––––––––
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        # 200 with an empty body (204 scenario) triggers this
        raise ZohoApiError(
            f"Zoho search returned invalid JSON: {exc} — body: {response.text}"
        ) from exc


@ensure_authorized
def searchZohoContacts(contactID: str) -> Dict[str, Any]:
    """
    Look up a Zoho record by its ID.

    Raises
    ------
    ZohoApiError
        If the HTTP status is anything other than 200 OK, or if the body
        can’t be parsed as JSON.
    """
    headers = {"Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}"}
    url = f"{baseUrlContacts}{contactID}"
    print(f"url {url}")

    response = requestGet(headers=headers, url=url)
    print(f"response in searchZohoRecords {response}")  # e.g. <Response [204]>
    print(f'response.status_code {response.status_code}')

    #––– 1. Enforce exact-200 success –––––––––––––––––––––––––––––––––––
    if response.status_code == 204:
        raise ZohoApiError(
            f"Zoho search failed (HTTP {response.status_code}): empty response from search zoho contacts for {contactID} for url {url} "
        )

    #––– 2. Parse JSON safely –––––––––––––––––––––––––––––––––––––––––––
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        # 200 with an empty body (204 scenario) triggers this
        raise ZohoApiError(
            f"Zoho search returned invalid JSON: {exc} — body: {response.text}"
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
    print(f'response {submittedResponse}')

    submittedResponses = []
    submittedResponses = [response['id'] for response in submittedResponse.json()['data']] if len(submittedResponse.json()['data']) > 0 else []
    print(f'submittedResponses {len(submittedResponses)}')


    urlDead = f"{baseUrl}search?criteria=Submission_Status:equals:Dead"
    deadResponse = requestGet(headers=headers,url=urlDead)
    deadResponses = []
    deadResponses = [response['id'] for response in deadResponse.json()['data']] if len(deadResponse.json()['data']) > 0 else []
    print(f'deadResponses {len(deadResponses)}')

    urlNew = f"{baseUrl}search?criteria=Submission_Status:equals:New"
    newResponse = requestGet(headers=headers,url=urlNew)
    newResponses = []
    newResponses = [response['id'] for response in newResponse.json()['data']] if len(newResponse.json()['data']) > 0 else []
    print(f'newResponses {len(newResponses)}')
    print(f'newResponse {newResponse.json()}')



    
    return {'response': submittedResponses + deadResponses + newResponses}


#TODO TEST
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