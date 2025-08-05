from functions.api.naa import postCase, closeCase, getCaseByID, uploadFile
from functions.api.zoho import (
    searchZohoRecords,
    addCaseIDToZohoRecord,
    getListOfSyncIds,
    updateResults,
    getFileFromZoho,
    searchZohoContacts,
)
import base64
from requests.exceptions import HTTPError


def retry_once(fn):
    """
    Decorator: call the function, retry once on HTTPError or any Exception,
    then propagate the last error if it still fails.
    """

    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in (1, 2):
            try:
                return fn(*args, **kwargs)
            except (HTTPError, Exception) as e:
                last_exc = e
                if attempt == 2:
                    # After second failure, re-raise
                    raise
        # Should never reach here

    return wrapper


def extract_fields_from_zoho(zohoDetails: dict, name: str, requestId: str) -> dict:
    try:
        defendantPlantiff = False
        caseClientName = name
        data0 = zohoDetails["data"][0]
        print("hi")

        outCourtState = data0["State"]
        outCourtCity = data0["City"]
        outCourtName = data0["Court_Name"]
        outCourtAddress = data0["Address"]
        outCourtZip = data0["Zip_Code"]
        hearingType = data0["Pick_List_5"]
        detailedInstructions = data0["Desired_Result"]
        # detailedInstructions = "Enter (1) any special instructions for this hearing and (2) desired results."

        attorneyRecord = data0["Attorney_of_Record"]
        fileNumber = data0["Client_Reference"]
        caseName = data0["Case_Name1"]
        caseNumber = data0["Case_Number"]

        # Normalize county field
        outCourtCounty = data0["County2"]["name"]
        if ":" in outCourtCounty:
            outCourtCounty = outCourtCounty.split(":", 1)[1].strip()

        # Parse and format hearingDate
        hearingTime = str(data0["Twenty_Four_Hr_Hearing_Time"])
        date_part, time_part = hearingTime.split(" ")
        hour, minute = time_part.split(":")[:2]
        hour = hour.zfill(2)
        minute = minute.zfill(2)
        hearingDate = f"{date_part}T{hour}:{minute}:00"

        return {
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
            "attorneyRecord": attorneyRecord,
            "caseName": caseName,
            "caseClientName": caseClientName,
            "caseNumber": caseNumber,
        }
    except KeyError:
        return None


@retry_once
def _core_create_case_from_zoho(matterID: int) -> dict:
    # 1) Lookup Zoho record
    recs = searchZohoRecords(matterID)
    if "error" in recs:
        raise HTTPError(recs["error"], response=recs)
    print("hello world")

    # 2) Lookup contact name
    lookupVal = recs["data"][0]["Matter"]["id"]
    nameRes = searchZohoContacts(lookupVal)
    print(nameRes)
    if "error" in nameRes:
        raise HTTPError(nameRes["error"], response=nameRes)
    name = nameRes["data"][0]["Contact_Name"]["name"]
    print("hello world1111111")
    print(name)

    # 3) Extract fields
    zohoDetails = extract_fields_from_zoho(recs, name, matterID)
    if zohoDetails is None:
        raise KeyError("Missing Zoho fields")
    print(zohoDetails)

    # 4) Create case in NAA
    caseID = postCase(
        outCourtState=zohoDetails["outCourtState"],
        outCourtCounty=zohoDetails["outCourtCounty"],
        outCourtCity=zohoDetails["outCourtCity"],
        outCourtName=zohoDetails["outCourtName"],
        outCourtAddress=zohoDetails["outCourtAddress"],
        outCourtZip=zohoDetails["outCourtZip"],
        hearingType=zohoDetails["hearingType"],
        hearingDate=zohoDetails["hearingDate"],
        fileNumber=zohoDetails["fileNumber"],
        defendantPlantiff=zohoDetails["defendantPlantiff"],
        detailedInstructions=zohoDetails["detailedInstructions"],
        attorneyRecord=zohoDetails["attorneyRecord"],
        caseName=zohoDetails["caseName"],
        caseClientName=zohoDetails["caseClientName"],
        caseNumber=zohoDetails["caseNumber"],
    )
    if caseID.get("error") is not None:
        raise HTTPError(
            f"Case not created for {matterID}: {caseID['error']}", response=caseID
        )

    # 5) Write back to Zoho
    addCaseIDToZohoRecord(matterID, str(caseID))

    return {"response": caseID, "statusCode": 200}


def create_case_from_zoho(matterID: int) -> dict:
    try:
        return _core_create_case_from_zoho(matterID)
    except HTTPError as e:
        # pull statusCode from response dict if present
        status = (
            e.response.get("statusCode", 500) if isinstance(e.response, dict) else 500
        )
        return {"error": str(e), "statusCode": status}
    except Exception as e:
        return {"error": str(e), "statusCode": 500}


@retry_once
def _core_close_case_from_zoho(matterID: int) -> dict:
    zohoDetails = searchZohoRecords(matterID)
    if "error" in zohoDetails:
        raise HTTPError(zohoDetails["error"], response=zohoDetails)

    caseID = zohoDetails["data"][0]["NAAM_CaseID"]
    result = closeCase(caseID)
    if not isinstance(result, str):
        raise ValueError(f"closeCase returned error: {result}")

    return {"response": result, "statusCode": 200}


def close_case_from_zoho(matterID: int) -> dict:
    try:
        return _core_close_case_from_zoho(matterID)
    except Exception as e:
        return {"error": str(e), "statusCode": 500}


@retry_once
def _core_get_doc_from_zoho_upload_to_naa(
    docID: str, docName: str, caseID: str
) -> dict:
    # 1) fetch from Zoho
    res0 = getFileFromZoho(docID)
    raw = res0["response"]

    # 2) decode if base64
    if isinstance(raw, str):
        file_bytes = base64.b64decode(raw)
    elif isinstance(raw, (bytes, bytearray)):
        file_bytes = bytes(raw)
    else:
        raise TypeError(f"Unexpected payload type: {type(raw)}")

    # 3) upload to NAA
    return uploadFile(caseID, file_bytes, docName)


def get_doc_from_zoho_upload_to_naa(docID: str, docName: str, caseID: str) -> dict:
    try:
        return _core_get_doc_from_zoho_upload_to_naa(docID, docName, caseID)
    except Exception as e:
        return {"error": str(e), "statusCode": 500}


def sync_cases():
    try:
        matterIds = getListOfSyncIds()["response"]
        for matterId in matterIds:
            zohoRec = searchZohoRecords(matterId)
            caseID = zohoRec["data"][0].get("NAAM_CaseID")
            if caseID is not None:
                naaCaseDetails = getCaseByID(caseID)
                caseStatus = naaCaseDetails["caseStatus"]
                results = naaCaseDetails.get("detailedResults", "")
                print("naaCaseDetails:", naaCaseDetails)
                status_map = {
                    1: "Available",
                    2: "Assigned",
                    3: "Closed",
                    5: "Cancelled",
                    6: "Pending",
                    7: "Open",
                    9: "Soft Lock",
                }
                updateResults(matterId, status_map.get(caseStatus, "Unknown"), results)
    except Exception as e:
        return {"error": str(e)}
