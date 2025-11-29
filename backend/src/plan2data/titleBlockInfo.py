import json
import src.plan2data.extractionLogictitleBlock as title_block
import src.plan2data.mistralConnection as mistral 


### workflow to identify title block in floorplan and extract the keyfeatures (Keyfeatures are shown in terminal)
def get_title_block_info(path):
    is_succesful = False
    method = "hybrid"
    output= json.loads(extract_title_block_info(path))
    if output["confidence"] < 0.5:
        print("Ai localization started")
        output = json.loads(extract_title_block_info_with_ai(path))
    if output["confidence"] > 0.5:
        is_succesful= True
    confidence = output["confidence"]
    return output, method, is_succesful, confidence


def extract_title_block_info(image_path):
    text_title_block = title_block.extract_text_titleblock(image_path)
    mistral_response_content = mistral.call_mistral_for_content_extraction(text_title_block)
    return mistral_response_content

def extract_title_block_info_with_ai(image_path):
    mistral_response = mistral.call_mistral_for_titleblock_extraction_from_image(image_path)
    return mistral_response





