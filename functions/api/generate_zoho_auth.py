import os
from dotenv import load_dotenv
import requests
import json

# Path to your JSON creds file
CONFIG_FILE = 'credentials/credentials.json'

# Load CLIENT_ID, CLIENT_SECRET and REFRESH_TOKEN from .env
load_dotenv(override=True)
CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHOCRM_REFRESH_TOKEN")


def json_read_a_write(mode='r', new_json=None, json_file=CONFIG_FILE):
    """
    mode: 'r' to read, 'w' to overwrite
    new_json: dict to write when mode='w'
    returns: the JSON content (after reading or writing)
    """
    # If reading but file doesn't exist, create it as empty JSON
    if mode == 'r' and not os.path.exists(json_file):
        os.makedirs(os.path.dirname(json_file), exist_ok=True)
        with open(json_file, 'w') as f:
            json.dump({}, f, indent=4)

    if mode == 'r':
        with open(json_file, 'r') as f:
            return json.load(f)
    elif mode == 'w' and isinstance(new_json, dict):
        # Ensure directory exists
        os.makedirs(os.path.dirname(json_file), exist_ok=True)
        with open(json_file, 'w') as f:
            json.dump(new_json, f, indent=4)
        return new_json
    else:
        raise ValueError("Invalid arguments to json_read_a_write")


def zoho_generate_authtoken(credential_file_name=CONFIG_FILE):
    # 1) Load existing credentials JSON (will create file if missing)
    creds = json_read_a_write(mode='r', json_file=credential_file_name)

    # 2) Hit Zoho’s token endpoint
    resp = requests.post(
        "https://accounts.zoho.com/oauth/v2/token",
        params={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        }
    )
    data = resp.json()

    # 3) Check for errors
    if resp.status_code != 200 or 'access_token' not in data:
        err = data.get('error_description') or data.get('error') or resp.text
        return f"Error generating ZohoCRM access token: {err}"

    # 4) Update our credentials file
    creds['access_token'] = data['access_token']
    creds['expires_in']  = data['expires_in']
    json_read_a_write(mode='w', new_json=creds, json_file=credential_file_name)

    return "Success generating ZohoCRM access token"
