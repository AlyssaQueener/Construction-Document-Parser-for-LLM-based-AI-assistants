import src.plan2data.titleBlockInfo as parser
import src.validation.titleblock.llm_as_a_judge as llm_judge


image_path = "src/validation/titleblock/testdata/floorplan-test_page1.png"
image_path_1 = "src/validation/titleblock/testdata/floorplan-test-1_page1.png"
image_path_2 = "src/validation/titleblock/testdata/floorplan-test-2_page1.png"

validation_path = "src/validation/titleblock/testdata/floorplan-test.json"
validation_path_1 = "src/validation/titleblock/testdata/floorplan-test-1.json"
validation_path_2 = "src/validation/titleblock/testdata/floorplan-test-2.json"

result = parser.get_title_block_info(image_path)
#result_1 = parser.get_title_block_info(image_path_1)
#result_2 = parser.get_title_block_info(image_path_2)

print("Result of first example")
print(result)
print("Result of second example")
#print(result_1)
print("Result of third example")
#print(result_2)

print("Validation Results:")
#print("1. Example:")
print(llm_judge.llm_as_a_judge_titleblock(validation_path, result))
#print("2. Example:")
#print(llm_judge.llm_as_a_judge_titleblock(validation_path_1, result_1))
#print("3. Example:")
##print(llm_judge.llm_as_a_judge_titleblock(validation_path_2, result_2))

