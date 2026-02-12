import src.plan2data.titleBlockInfo as parser
import src.validation.Floorplan.titleblock.llm_as_a_judge as llm_judge
import src.plan2data.helper as helper

path1 = "Cluttered 01_page1.png"
path2 = "Cluttered 02_page1.png"
path3 = "Cluttered 03_page1.png"





#print("Cluttered 1")
#print("Without AI")
#print(parser.extract_title_block_info(path1))
#print("With AI")
#print(parser.extract_title_block_info_with_ai(path1))

#print("Cluttered 2")
#print("Without AI")
#print(parser.extract_title_block_info(path2))
#print("With AI")
#print(parser.extract_title_block_info_with_ai(path2))


#print("Cluttered 3")
#print("Without AI")
#print(parser.extract_title_block_info(path3))
#print("With AI")
#print(parser.extract_title_block_info_with_ai(path3))


########Validation#######

##GroundTruths
g_path1 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/ground_truth_titleblock/cluttered 01_titleblock.json"
g_path2 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/ground_truth_titleblock/cluttered 02_titleblock.json"
g_path3 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/ground_truth_titleblock/cluttered 03_titleblock.json"

###Parsing Results
###Hybrid
hybrid_path1 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/parsing_result_titleblock/hybrid/clutterd 01 hybrid.json"
hybrid_path2 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/parsing_result_titleblock/hybrid/clutterd 02 hybrid.json"
hybrid_path3 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/parsing_result_titleblock/hybrid/clutterd 03 hybrid.json"

##Full Ai 
ai_path1 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/parsing_result_titleblock/full ai/cluttered 01 full ai.json"
ai_path2 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/parsing_result_titleblock/full ai/cluttered 02 full ai.json"
ai_path3 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/parsing_result_titleblock/full ai/cluttered 03 full ai.json"




#Clutterplan 1

print("Clutterplan ")
print("Hybrid Parser Validation Result:")
print(llm_judge.llm_as_a_judge_titleblock(g_path3,hybrid_path3))
print("Ai Parser Validation Result:")
print(llm_judge.llm_as_a_judge_titleblock(g_path3,ai_path3))
