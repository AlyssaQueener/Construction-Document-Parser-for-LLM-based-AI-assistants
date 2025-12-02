import src.gantt2data.ganttParser as parser
import src.validation.Gantt.validator as validator


path = "src/validation/Gantt/testdata/result-test-tab.json"
path_1 = "src/validation/Gantt/testdata/result-test-tab-1.json"
path_2 = "src/validation/Gantt/testdata/result-test-tab-2.json"

path_v = "src/validation/Gantt/testdata/result-test-vis.json"
path_v_1 = "src/validation/Gantt/testdata/result-test-vis-3.json"
#### here i sended beginning of data frame with image
path_v_1_1 = "src/validation/Gantt/testdata/result-test-vis-3-1.json"
### chunked image
path_v_1_chunk = "src/validation/Gantt/testdata/result-test-vis-3-with-chunking.json"
path_v_1_chunk_smaller = "src/validation/Gantt/testdata/result-test-vis-3-smaller-chunking.json"

validation_path = "src/validation/Gantt/testdata/test-tabular.json"
validation_path_1 = "src/validation/Gantt/testdata/test-tabular-1.json"
validation_path_2 = "src/validation/Gantt/testdata/test-tabular-2.json"

validation_v ="src/validation/Gantt/testdata/test-visual.json"
validation_v_1 ="src/validation/Gantt/testdata/test-visual-3.json"


print(validator.validate(validation_v_1, path_v_1_chunk_smaller))