import src.plan2data.titleBlockInfo as parser
import src.plan2data.helper as helper
import src.validation.titleblock.validator as validator

### workflow to identify title block in floorplan and extract the keyfeatures (Keyfeatures are shown in terminal)

#image_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf_page1.png"
#image_path = "examples/FloorplansAndSectionViews/floorplan1.png"
image_path = "src/validation/titleblock/testdata/floorplan-test_page1.png"
image_path_1 = "src/validation/titleblock/testdata/floorplan-test-1_page1.png"
image_path_2 = "src/validation/titleblock/testdata/floorplan-test-2_page1.png"

validation_path_1 = "src/validation/titleblock/testdata/floorplan-test-1.json"

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

#result = parser.get_title_block_info(image_path_1)
#print(result)
#print(type(result))
result1 = {"client": "Landesbetrieb für Straßenbau", "creation_date": '10.06.2025', 'drawing_name/ plan type': 'Grundriss Erdgeschoss', 'project_name': 'LFS Lebach - Neubau Verwaltungsgebäude', 'location': 'Schlesierallee, 66822 Lebach', 'scale': '1:100', 'architect': None}
#validator.validate(validation_path_1, result1)
#helper.convert_pdf2img(pdf_path)
validator.test2(validation_path_1, result1)
