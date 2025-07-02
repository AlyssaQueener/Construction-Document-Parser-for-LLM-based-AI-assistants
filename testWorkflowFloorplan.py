import src.plan2data.titleBlock as title_block
import src.plan2data.mistralConnection as mistral
import src.plan2data.helper as helper
import testWorkflowFloorplanForApi as test


### workflow to identify title block in floorplan and extract the keyfeatures (Keyfeatures are shown in terminal)

#image_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf_page1.png"
image_path = "examples/FloorplansAndSectionViews/floorplan1.png"
#image_path = "examples/FloorplansAndSectionViews/floorplan2.png"

#mistral_response = mistral.call_mistral_for_titleblock_location(image_path)
#print("Ai title block localization:")
#print(mistral_response)
#horizontal_boundry_percentage, vertical_boundry_percentage, greater_then_horizontal, greater_then_vertical = helper.prepare_for_titleblock_extraction(mistral_response)
#title_block_region = title_block.init_title_block_extraction_with_ai_localization(image_path, horizontal_boundry_percentage, greater_then_horizontal, vertical_boundry_percentage, greater_then_vertical)
#print(title_block_region)
#title_block.visualize_results(image_path, title_block_region)
#text_title_block = title_block.extract_text_titleblock(image_path,title_block_region)
#mistral_response_content = mistral.call_mistral_for_content_extraction(text_title_block)

#print(mistral_response_content)

print(test.get_title_block_info(image_path))


