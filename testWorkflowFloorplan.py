import src.plan2data.titleBlock as title_block
import src.plan2data.mistralConnection as mistral


### workflow to identify title block in floorplan and extract the keyfeatures (Keyfeatures are shown in terminal)

image_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf_page1.png"

title_block_region = title_block.init_title_block_extraction(image_path)
text_title_block = title_block.extract_text_titleblock(image_path, title_block_region)
promt = mistral.create_extraction_prompt_with_examples(text_title_block)
mistral_response = mistral.call_mistral_return_json(promt)
print("Key Features of floor plan title block:")
print(mistral_response)


