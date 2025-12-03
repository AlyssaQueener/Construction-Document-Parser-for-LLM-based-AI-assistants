import requests
import os
import src.plan2data.mistralConnection as mistral 
import src.plan2data.helper as helper

### workflow to identify title block in floorplan and extract the keyfeatures
def get_title_block_info(path):
    import json
    is_succesful = False
    method = "hybrid"
    
    output_str = extract_title_block_info(path)
    
    # Handle None/failed extraction
    if output_str is None:
        is_succesful = False
        return {"Parsing": "Failed"}, method, is_succesful, None
    
    output = json.loads(output_str)
    
    if output["confidence"] < 0.5:
        print("AI localization started")
        output_str_ai = extract_title_block_info_with_ai(path)
        if output_str_ai is not None:
            output = json.loads(output_str_ai)
    
    if output["confidence"] > 0.5:
        is_succesful = True
    
    confidence = output["confidence"]
    return output, method, is_succesful, confidence


def extract_title_block_info(image_path):
    try:
        print("Starting OCR extraction...")
        text_title_block = call_ocr_service(image_path)
        
        # Check if we got text back
        if not text_title_block or text_title_block.strip() == "":
            print("OCR returned empty text")
            return None
        
        print(f"OCR extracted text (length: {len(text_title_block)})")
        mistral_response_content = mistral.call_mistral_for_content_extraction(text_title_block)
        return mistral_response_content
        
    except Exception as e:
        print(f"Calling OCR failed: {str(e)}")
        import traceback
        traceback.print_exc()  # This will show you the full error
        return None


def extract_title_block_info_with_ai(image_path):
    try:
        mistral_response = mistral.call_mistral_for_titleblock_extraction_from_image(image_path)
        return mistral_response
    except Exception as e:
        print(f"AI extraction failed: {str(e)}")
        return None


def call_ocr_service(image_path, ocr_service_url=None, max_retries=2):
    """
    Call the OCR microservice to extract text from titleblock
    """
    if ocr_service_url is None:
        ocr_service_url = os.environ.get('OCR_SERVICE_URL', 'http://127.0.0.1:8000')
    
    print(f"Calling OCR service at: {ocr_service_url}")
    
    for attempt in range(max_retries):
        try:
            # Increase timeout significantly for free tier cold starts
            timeout = 120 if attempt == 0 else 180  # 2 min first try, 3 min retry
            
            print(f"Attempt {attempt + 1}/{max_retries} with {timeout}s timeout...")
            
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post(
                    f"{ocr_service_url}/ocr",
                    files=files,
                    timeout=timeout
                )
            
            print(f"OCR service response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                text = data.get('text', '')
                print(f"Successfully received text from OCR (length: {len(text)})")
                return text
            else:
                raise Exception(f"OCR service returned status code {response.status_code}: {response.text}")
        
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Timeout on attempt {attempt + 1}, retrying...")
                continue
            else:
                raise Exception("OCR service request timed out after all retries")
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                print(f"Connection error on attempt {attempt + 1}, retrying...")
                continue
            else:
                raise Exception(f"Could not connect to OCR service at {ocr_service_url}: {str(e)}")
        except Exception as e:
            # Don't retry on other exceptions
            raise Exception(f"Error calling OCR service: {str(e)}")
    
    raise Exception("OCR service failed after all retries")