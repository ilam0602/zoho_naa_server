import os
from dotenv import load_dotenv
from functions.helpers.constants import loginNAAPostUrl,getNAACasesUrl
from functions.helpers.helpers import requestGet, requestPost,requestPatch,requestPut
from functions.api.generate_zoho_auth import zoho_generate_authtoken
import json
from functools import wraps
from requests.exceptions import HTTPError
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


#search zoho records
@ensure_authorized
def searchZohoRecords(matterID:int) -> dict:
    formatToken = f"Zoho-oauthtoken {ACCESS_TOKEN}"

    headers = {
        "Authorization" :formatToken 
    }
    # url = f"{baseUrl}search?criteria=id:equals:{matterID}"
    url = f"{baseUrl}search?criteria=id:equals:{matterID}"
    print(f'url {url}')

    response = requestGet(headers=headers,url=url)
    return response.json()




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

