import json
import src.plan2data.extractionLogictitleBlock as title_block
import src.plan2data.mistralConnection as mistral 
import src.plan2data.helper as helper 


### workflow to identify title block in floorplan and extract the keyfeatures (Keyfeatures are shown in terminal)
def get_neighbouring_rooms_with_ai(path):
    is_succesful = False
    method = "ai"
    output= json.loads(extract_neighbouring_rooms_with_ai(path))
    if output["confidence"] > 0.5:
        is_succesful= True
    confidence = output["confidence"]
    return output, method, is_succesful, confidence
############
def get_full_floorplan_metadata_with_ai(path): 
    is_succesful = False
    method = "ai"
    output= json.loads(extract_full_floorplan_metadata_with_ai(path))
    # Extract both confidence scores from the nested structure
    titleblock_confidence = output.get("titleBlock", {}).get("confidence", 0.0)
    room_confidence = output.get("roomAdjacency", {}).get("confidence", 0.0)
    
    # Use average confidence or minimum confidence depending on your needs
    confidence = (titleblock_confidence + room_confidence) / 2  # Average
    # OR use minimum: confidence = min(titleblock_confidence, room_confidence)
    
    if confidence > 0.5:
        is_succesful = True
    
    return output, method, is_succesful, confidence


def extract_neighbouring_rooms_with_ai(image_path):
    mistral_response = mistral.call_mistral_for_room_adjacency_extraction(image_path)
    return mistral_response

def extract_full_floorplan_metadata_with_ai(image_path):
    mistral_response = mistral.call_mistral_for_floorplan_extraction_from_image(image_path)
    return mistral_response


