import src.plan2data.mistralConnection as mistral 
import src.plan2data.extractionLogictitleBlock as extractor
import json
### workflow to identify title block in floorplan and extract the keyfeatures
def get_title_block_info(path):
    
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
    
    if output["confidence"] > 0.4:
        is_succesful = True
    
    confidence = output["confidence"]
    return output, method, is_succesful, confidence


def extract_title_block_info(image_path):
    try:
        print("Starting OCR extraction...")
        text_title_block = extractor.extract_text_titleblock(image_path)
        
        
        mistral_response_content = mistral.call_mistral_for_content_extraction(text_title_block)
        
        return mistral_response_content
        
    except Exception as e:
        print(f"OCR Extraction failed: {str(e)}") # This will show you the full error
        return None


def extract_title_block_info_with_ai(image_path):
    try:
        mistral_response = mistral.call_mistral_for_titleblock_extraction_from_image(image_path)
        return mistral_response
    except Exception as e:
        print(f"AI extraction failed: {str(e)}")
        return None


