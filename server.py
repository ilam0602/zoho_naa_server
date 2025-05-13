from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from functions.connector_fn import create_case_from_zoho,close_case_from_zoho

app = Flask(__name__)
load_dotenv(override=True)
SERVER_PASS = os.getenv("SERVER_PASS")

def checkAuth(token: str):
    """
    Check if the provided token matches the server password.
    """
    print(f"Token: {token}")
    print(f"Server Password: {SERVER_PASS}")
    return token == SERVER_PASS

@app.route('/createNAACaseFromZoho', methods=['POST'])
def create_naa_case_endpoint():
    # Extract token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    # Support 'Bearer <token>' format
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        token = parts[1]
    else:
        token = auth_header

    if not checkAuth(token):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)
    if not data or 'matterID' not in data:
        return jsonify({"error": "Missing 'matterID' in request body"}), 400

    try:
        matterID = int(data['matterID'])
    except (ValueError, TypeError):
        return jsonify({"error": "'matterID' must be an integer"}), 400

    result = create_case_from_zoho(matterID)
    print(f'result= {result}')

    # extract statusCode if provided, else default
    status = result.pop('statusCode', None)
    if status is None:
        status = 200 if 'response' in result else 500

    return jsonify(result), status
@app.route('/closeNAACaseFromZoho', methods=['POST'])
def close_naa_case_endpoint():
    # Extract token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    # Support 'Bearer <token>' format
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        token = parts[1]
    else:
        token = auth_header

    if not checkAuth(token):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)
    if not data or 'matterID' not in data:
        return jsonify({"error": "Missing 'matterID' in request body"}), 400

    try:
        matterID = int(data['matterID'])
    except (ValueError, TypeError):
        return jsonify({"error": "'matterID' must be an integer"}), 400

    result = close_case_from_zoho(matterID)
    print(f'result= {result}')

    # extract statusCode if provided, else default
    status = result.pop('statusCode', None)
    if status is None:
        status = 200 if 'response' in result else 500

    return jsonify(result), status

if __name__ == '__main__':
    app.run(debug=True, port=8081)
    #prod
    # app.run(host='0.0.0.0', port=8765, debug=True)
