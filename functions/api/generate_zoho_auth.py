import requests
import json

CONFIG_FILE ='credentials/credentials.json'

def zoho_generate_authtoken(credential_file_name=CONFIG_FILE):
    f = json_read_a_write(json_file = credential_file_name)
    print(f)
    print(credential_file_name)
    response = requests.post(
        f"https://accounts.zoho.com/oauth/v2/token?client_id={f['client_id']}&client_secret={f['client_secret']}&refresh_token={f['refresh_token']}&grant_type=refresh_token"
    ).json()
    try:
        f['access_token'] = response['access_token']
        f['expires_in'] = response['expires_in']
        with open(credential_file_name, 'w') as file:
            json.dump(f, file, indent=4)
        return "Success generating ZohoCRM access token"
    except:
        return "Error generating ZohoCRM access token"

def json_read_a_write(type='r', new_json={}, json_file=CONFIG_FILE):
    json_body = {}
    print(json_file)
    print(f'type {type}')
    if type == "r":
        with open(json_file, type) as file:
            json_body = json.loads(file.read())
            print(json_body)
    if type == "w":
        with open(json_file, type) as file:
            json_body = new_json
            json.dump(new_json, file, indent=4)
    return json_body
