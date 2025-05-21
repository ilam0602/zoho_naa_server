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

def create_case_from_zoho(matterID: int) -> dict:
    """
    Pulls details from Zoho, posts to NAA and writes the new NAA caseID back to Zoho.
    """
    try:
        zohoDetails = extract_fields_from_zoho(
            searchZohoRecords(matterID),
            matterID
        )

        # create on NAA
        resNAA = postCase(
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
        print('hello world')

        caseID = resNAA
        print(f'NAA caseID: {caseID}')
        if type(caseID) != int:
            return {"error": caseID.get('error')}

        # write the new caseID back to Zoho
        _ = addCaseIDToZohoRecord(matterID, str(caseID))

        return {"response": caseID, "statusCode": 200}

    except Exception as e:
        print(f"Error in create_case_from_zoho: {e}")
        return {"error": str(e)}

def close_case_from_zoho(matterID :int) -> dict:
    try:
        zohoDetails = searchZohoRecords(matterID)['data'][0]
        print('zohoDetails',zohoDetails)
        caseID = zohoDetails['NAAM_CaseID']
        print('caseID',caseID)
        close_case_from_zoho = closeCase(caseID)
        print(f'close_case_from_zoho {close_case_from_zoho}')
        if type(close_case_from_zoho) != str:
            return {"error": close_case_from_zoho.get('error'), "statusCode":400}
        return {"response": close_case_from_zoho, "statusCode": 200}

    except Exception as e:
        return {"error": str(e)}

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




