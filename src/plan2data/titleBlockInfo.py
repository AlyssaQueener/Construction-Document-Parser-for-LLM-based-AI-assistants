import json
import src.plan2data.extractionLogicTitleBlockEasyOcr as title_block
import src.plan2data.mistralConnection as mistral 
import src.plan2data.helper as helper 


### workflow to identify title block in floorplan and extract the keyfeatures (Keyfeatures are shown in terminal)
def get_title_block_info(path):
    output_with_ai = extract_title_block_info_with_ai(path)
    output_without_ai = extract_title_block_info(path)
    final_output = compare_results(output_with_ai,output_without_ai)
    return final_output

def compare_results(output_with_ai,output_without_ai):
    ai_ouput = json.loads(output_with_ai)
    non_ai_output = json.loads(output_without_ai)
    for i in ai_ouput:
        if ai_ouput[i] == None and non_ai_output[i] !=None:
            ai_ouput[i] = non_ai_output[i]
    return ai_ouput

def extract_title_block_info(image_path):
    title_block_region = title_block.init_title_block_extraction(image_path)
    text_title_block = title_block.extract_text_titleblock(image_path,title_block_region)
    mistral_response_content = mistral.call_mistral_for_content_extraction(text_title_block)
    return mistral_response_content

def extract_title_block_info_with_ai(image_path):
    mistral_response = mistral.call_mistral_for_titleblock_location(image_path)
    horizontal_boundry_percentage, vertical_boundry_percentage, greater_then_horizontal, greater_then_vertical = helper.prepare_for_titleblock_extraction(mistral_response)
    title_block_region = title_block.init_title_block_extraction_with_ai_localization(image_path, horizontal_boundry_percentage, greater_then_horizontal, vertical_boundry_percentage, greater_then_vertical)
    text_title_block = title_block.extract_text_titleblock(image_path,title_block_region)
    mistral_response_content = mistral.call_mistral_for_content_extraction(text_title_block)
    return mistral_response_content





