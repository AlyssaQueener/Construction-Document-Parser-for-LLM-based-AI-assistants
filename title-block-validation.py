import src.plan2data.titleBlockInfo as parser
import src.validation.Floorplan.titleblock.llm_as_a_judge as llm_judge
import src.plan2data.helper as helper

path1 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/Cluttered 01.pdf"
path2 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/Cluttered 02.pdf"
path3 = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/Cluttered 03.pdf"



image1 = helper.convert_pdf2img(path1)
image2 = helper.convert_pdf2img(path2)
image3 = helper.convert_pdf2img(path3)