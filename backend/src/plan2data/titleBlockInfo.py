import json
import src.plan2data.extractionLogictitleBlock as title_block
import src.plan2data.mistralConnection as mistral 
import src.plan2data.helper as helper

### workflow to identify title block in floorplan and extract the keyfeatures (Keyfeatures are shown in terminal)
def get_title_block_info(path):
    is_succesful = False
    method = "hybrid"
    output= json.loads(extract_title_block_info(path))
    if output == None:
        is_succesful = False
        return {"Parsing":"Failed"}, method, is_succesful, None
    if output["confidence"] < 0.5 and output != None:
        print("Ai localization started")
        output = json.loads(extract_title_block_info_with_ai(path))
    if output["confidence"] > 0.5 and output != None:
        is_succesful= True
    confidence = output["confidence"]
    return output, method, is_succesful, confidence


def extract_title_block_info(image_path):
    #text_title_block = title_block.extract_text_titleblock(image_path)
    try:
        text_title_block = call_ocr_service(image_path)
        mistral_response_content = mistral.call_mistral_for_content_extraction(text_title_block)
    except:
        print("Calling OCR failed")
        return None
    return mistral_response_content

def extract_title_block_info_with_ai(image_path):
    mistral_response = mistral.call_mistral_for_titleblock_extraction_from_image(image_path)
    return mistral_response

def call_ocr_service(image_path, ocr_service_url=None):
    import requests
    import os
    """
    Call the OCR microservice to extract text from titleblock
    """
    if ocr_service_url is None:
        ocr_service_url = os.environ.get('OCR_SERVICE_URL', 'http://127.0.0.1:8000')
    
    try:
        print("Calling OCR")
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(
                f"{ocr_service_url}/ocr",
                files=files,
                timeout=60
            )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('text', '')
        else:
            raise Exception(f"OCR service returned status code {response.status_code}: {response.text}")
    
    except requests.exceptions.Timeout:
        raise Exception("OCR service request timed out")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Could not connect to OCR service at {ocr_service_url}")
    except Exception as e:
        raise Exception(f"Error calling OCR service: {str(e)}")





