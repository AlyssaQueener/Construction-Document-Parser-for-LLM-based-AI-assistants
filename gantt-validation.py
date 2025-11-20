import src.gantt2data.ganttParser as parser
import src.validation.Gantt.validator as validator


path = "src/validation/Gantt/testdata/test-tabular.pdf"
path_1 = "src/validation/Gantt/testdata/test-tabular-1.pdf"
path_2 = "src/validation/Gantt/testdata/test-tabular-2.pdf"

path_v = "src/validation/Gantt/testdata/test-visual.pdf"

validation_path = "src/validation/Gantt/testdata/test-tabular.json"
validation_path_1 = "src/validation/Gantt/testdata/test-tabular-1.json"
validation_path_2 = "src/validation/Gantt/testdata/test-tabular.json"

validation_v ="src/validation/Gantt/testdata/test-visual.json"
#result = parser.get_title_block_info(image_path)
#result_1 = parser.get_title_block_info(image_path_1)
result_2 = parser.parse_gantt_chart(path_1, "tabular")
print(result_2)

result_v = parser.parse_gantt_chart(path_v,"visual")

print(validator.validate_visual(validation_v, result_v))