import json
import src.plan2data.extractionLogictitleBlock as title_block
import src.plan2data.mistralConnection as mistral 
import src.plan2data.helper as helper 


### workflow to identify title block in floorplan and extract the keyfeatures (Keyfeatures are shown in terminal)


def extract_neighbouring_rooms_with_ai(image_path):
    mistral_response = mistral.call_mistral_for_room_adjacency_extraction(image_path)
    return mistral_response

def extract_fill_floorplan_metadata_with_ai(image_path):
    mistral_response = mistral.call_mistral_for_floorplan_extraction_from_image(image_path)
    return mistral_response


