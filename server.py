from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import threading
import time

from functions.connector_fn import create_case_from_zoho, close_case_from_zoho, sync_cases,get_doc_from_zoho_upload_to_naa

app = Flask(__name__)
load_dotenv(override=True)
SERVER_PASS = os.getenv("SERVER_PASS")

def checkAuth(token: str):
    """
    Check if the provided token matches the server password.
    """
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

    data = request.get_json(force=True) if request.is_json else request.form.to_dict()
    print(f"Received data: {data}")
    print(request.is_json)
    print(request.form)
    if not data or 'matterID' not in data:
        return jsonify({"error": "Missing 'matterID' in request body"}), 400

    try:
        matterID = int(data['matterID'])
    except (ValueError, TypeError):
        return jsonify({"error": "'matterID' must be an integer"}), 400

    result = create_case_from_zoho(matterID)
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

    print(request.is_json)
    print(request.form)
    data = request.get_json(force=True) if request.is_json else request.form.to_dict()
    if not data or 'matterID' not in data:
        return jsonify({"error": "Missing 'matterID' in request body"}), 400

    try:
        matterID = int(data['matterID'])
    except (ValueError, TypeError):
        return jsonify({"error": "'matterID' must be an integer"}), 400

    result = close_case_from_zoho(matterID)
    status = result.pop('statusCode', None)
    if status is None:
        status = 200 if 'response' in result else 500

    return jsonify(result), status

@app.route('/uploadDocsFromZoho', methods=['POST'])
def upload_docs_endpoint():
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

    data = request.get_json(force=True) if request.is_json else request.form.to_dict()



    #TODO START HERE
    if not data or 'record_id' not in data or 'NAAM_CaseID' not in data or 'attachments' not in data:
        return jsonify({"error": "Missing params in request body"}), 400

    try:
        attachments = data['attachments']
        recordIDs = data['record_id']
        caseID = data['NAAM_CaseID']
        
    except (ValueError, TypeError):
        return jsonify({"error": "'matterID' must be an integer"}), 400
    
    for i in attachments:
        result = get_doc_from_zoho_upload_to_naa(i['document_id'], i['document_name'],caseID)
        status = result.pop('statusCode', None)
        if status is None:
            status = 200 if 'response' in result else 500

    return {'response':f'successfully uploaded {len(attachments)} docs'if status == 200 else 'error'}, status

def _background_sync_loop():
    """Background thread: sync_cases every hour, forever."""
    while True:
        try:
            sync_cases()
        except Exception:
            app.logger.exception("Error during sync_cases")
        # Sleep for 3600 seconds (1 hour)
        time.sleep(3600)

def start_background_sync():
    """
    Spawn and start the daemon thread for hourly sync.
    Call this before app.run().
    """
    thread = threading.Thread(target=_background_sync_loop, daemon=True)
    thread.start()
    app.logger.info("Background sync thread started, will run every hour.")

if __name__ == '__main__':
    # Start hourly sync thread
    # start_background_sync()

    # Run Flask app
    app.run(debug=True, port=8081)
    # prod:
    # app.run(host='0.0.0.0', port=8765, debug=False)