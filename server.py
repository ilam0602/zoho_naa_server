from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import threading
import time
import json

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
    # 1) Auth as before
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    parts = auth_header.split()
    token = parts[1] if len(parts) == 2 and parts[0].lower() == 'bearer' else auth_header
    if not checkAuth(token):
        return jsonify({"error": "Unauthorized"}), 401

    # 2) Parse body
    if request.is_json:
        data = request.get_json(force=True)
    else:
        # pulling flat form fields
        data = {
            'record_id': request.form.get('record_id'),
            'NAAM_CaseID': request.form.get('NAAM_CaseID'),
        }
        attachments_raw = request.form.get('attachments')
        if not attachments_raw:
            return jsonify({"error": "Missing attachments in form data"}), 400
        try:
            data['attachments'] = json.loads(attachments_raw)
        except (TypeError, json.JSONDecodeError):
            return jsonify({"error": "Invalid JSON for attachments"}), 400

    # 3) Validate presence
    if not all(k in data for k in ('record_id', 'NAAM_CaseID', 'attachments')):
        return jsonify({"error": "Missing params in request body"}), 400

    # 4) Validate types
    try:
        record_id = int(data['record_id'])
        case_id   = int(data['NAAM_CaseID'])
        attachments = data['attachments']
        if not isinstance(attachments, list):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "'record_id' and 'NAAM_CaseID' must be integers, and attachments must be a list"}), 400

    # 5) Process each attachment
    last_status = None
    for attachment in attachments:
        # expect each attachment is a dict with those keys
        doc_id   = attachment.get('document_id')
        doc_name = attachment.get('document_name')
        if not doc_id or not doc_name:
            return jsonify({"error": "Each attachment must include document_id and document_name"}), 400

        result = get_doc_from_zoho_upload_to_naa(doc_id, doc_name, case_id)
        last_status = result.pop('statusCode', None)
        if last_status is None:
            last_status = 200 if 'response' in result else 500

    # 6) Return final outcome
    if last_status == 200:
        return jsonify({
            "response": f"successfully uploaded {len(attachments)} docs"
        }), 200
    else:
        return jsonify({"error": "Error uploading docs"}), last_status
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
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    # prod:
    # app.run(host='0.0.0.0', port=8765, debug=False)