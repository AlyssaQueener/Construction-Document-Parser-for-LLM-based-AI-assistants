import src.gantt2data.ganttParser as parser
import src.validation.Gantt.validator as validator


path = "src/validation/Gantt/testdata/result-test-tab.json"
path_1 = "src/validation/Gantt/testdata/result-test-tab-1.json"
path_2 = "src/validation/Gantt/testdata/result-test-tab-2.json"

path_v = "src/validation/Gantt/testdata/result-test-vis.json"

validation_path = "src/validation/Gantt/testdata/test-tabular.json"
validation_path_1 = "src/validation/Gantt/testdata/test-tabular-1.json"
validation_path_2 = "src/validation/Gantt/testdata/test-tabular-2.json"

validation_v ="src/validation/Gantt/testdata/test-visual.json"


print(validator.validate(validation_path_2, path_2))