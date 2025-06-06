from functions.api.naa import postCase,loginNAA,closeCase,getCaseByID
from functions.api.zoho import searchZohoRecords, addCaseIDToZohoRecord, getListOfSyncIds,updateResults




def extract_fields_from_zoho(zohoDetails:dict,requestId:str) -> dict:
    try:
        # Extract the required fields from the Zoho details
        # TODO MAKE SURE FIELD VALUES ARE CORRECT ON ZOHO SIDE
        # TODO FINALIZE ALL FIELDS ON NAA SIDE
        outCourtState = zohoDetails['data'][0]['State']
        outCourtCounty = zohoDetails['data'][0]['County2']['name']
        outCourtCity = zohoDetails['data'][0]['City']
        outCourtName = zohoDetails['data'][0]['Court_Name']
        outCourtAddress = zohoDetails['data'][0]['Address']
        outCourtZip = zohoDetails['data'][0]['Zip_Code']
        hearingType = zohoDetails['data'][0]['Pick_List_5']
        hearingDate = zohoDetails['data'][0]['Hearing_Date']
        fileNumber = zohoDetails['data'][0]['Case_Number']
        defendantPlantiff = True
        detailedInstructions = zohoDetails['data'][0]['Desired_Result']
        #look at this
        attorneyRecord= requestId

        return {
            'outCourtState': outCourtState,
            'outCourtCounty': outCourtCounty,
            'outCourtCity': outCourtCity,
            'outCourtName': outCourtName,
            'outCourtAddress': outCourtAddress,
            'outCourtZip': outCourtZip,
            'hearingType': hearingType,
            'hearingDate': hearingDate,
            'fileNumber': fileNumber,
            'defendantPlantiff': defendantPlantiff,
            'detailedInstructions': detailedInstructions,
            'attorneyRecord': attorneyRecord
        }
    except KeyError as e:
        print(f"Key error: {e}")
        return None

def _with_single_retry(fn, *args, **kwargs):
    """
    Helper → call `fn` once, retry once on any Exception.
    Returns the function’s normal result or raises the last error.

    NOTE: you can move this helper to a shared utils module.
    """
    for attempt in (1, 2):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            print(f"[{fn.__name__}] attempt {attempt} failed: {exc}")
            if attempt == 2:
                raise  # re-raise after second failure


def create_case_from_zoho(matterID: int) -> dict:
    """
    Pull details from Zoho, open the case in NAA, write the new caseID back to Zoho.
    Retries the whole flow once if it raises.
    """
    def _core() -> dict:           # ➊ inner fn keeps retry helper simple
        print("create_case_from_zoho – starting")
        zohoDetails = extract_fields_from_zoho(
            searchZohoRecords(matterID),
            matterID
        )

        # ❷ create on NAA
        caseID = postCase(
            outCourtState=zohoDetails['outCourtState'],
            outCourtCounty=zohoDetails['outCourtCounty'],
            outCourtCity=zohoDetails['outCourtCity'],
            outCourtName=zohoDetails['outCourtName'],
            outCourtAddress=zohoDetails['outCourtAddress'],
            outCourtZip=zohoDetails['outCourtZip'],
            hearingType=zohoDetails['hearingType'],
            hearingDate=zohoDetails['hearingDate'],
            fileNumber=zohoDetails['fileNumber'],
            defendantPlantiff=zohoDetails['defendantPlantiff'],
            detailedInstructions=zohoDetails['detailedInstructions'],
            attorneyRecord=zohoDetails['attorneyRecord']
        )
        print(f"NAA caseID: {caseID}")

        if not isinstance(caseID, int):
            # force an exception so the retry wrapper handles it
            raise ValueError(f"NAA returned non-int caseID: {caseID}")

        # ❸ write the new caseID back to Zoho
        addCaseIDToZohoRecord(matterID, str(caseID))

        return {"response": caseID, "statusCode": 200}

    # ❹ run with single retry
    try:
        return _with_single_retry(_core)
    except Exception as e:
        return {"error": str(e), "statusCode": 500}


def close_case_from_zoho(matterID: int) -> dict:
    """
    Close an existing NAA case using Zoho record linkage.
    Retries once on failure.
    """
    def _core() -> dict:
        zohoDetails = searchZohoRecords(matterID)['data'][0]
        caseID = zohoDetails['NAAM_CaseID']
        result = closeCase(caseID)

        if not isinstance(result, str):
            raise ValueError(f"closeCase returned error: {result}")

        return {"response": result, "statusCode": 200}

    try:
        return _with_single_retry(_core)
    except Exception as e:
        print(f"[close_case_from_zoho] second failure: {e}")
        return {"error": str(e), "statusCode": 500}


def sync_cases():
    try:
        #get list of matter ids
        matterIds = getListOfSyncIds()['response']
        for matterId in matterIds:
            #get naa case id from zoho record
            naaCaseID = searchZohoRecords(matterId)['data'][0]['NAAM_CaseID']
            print('naaCaseID',naaCaseID)
            #get naa case details
            if naaCaseID is not None:
                print(f"NAA case ID is not None for matter ID {matterId} {naaCaseID}")
                naaCaseDetails = getCaseByID(naaCaseID)

                #read case_status
                caseStatus = naaCaseDetails['caseStatus']
                caseStatusDict = {
                    1: 'Available',
                    2: 'Assigned',
                    3: 'Closed',
                    5: 'Cancelled',
                    6: 'Pending',
                    7: 'Open',
                    9: 'Soft Lock'
                }
                print('caseStatus',caseStatus)

                #update zoho record with naa case status
                res = updateResults(matterId,caseStatusDict[caseStatus])
                print('update results res',res)
            else:
                print(f"Error: NAA case ID is None for matter ID {matterId}")


    except Exception as e:
        return {"error": str(e)}




