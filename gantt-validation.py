import src.gantt2data.ganttParser as parser
import src.validation.Gantt.validator as validator

#Ground truth:
path = 'src/validation/Gantt/testdata/ground-truth/test-vis-excel-1.json'
path1 = 'src/validation/Gantt/testdata/ground-truth/test-vis-excel-2.json'
path2 = 'src/validation/Gantt/testdata/ground-truth/test-vis-excel-3.json'
path3 = 'src/validation/Gantt/testdata/ground-truth/test-vis-excel-4.json'


# Parsing Results
result_path = 'src/validation/Gantt/testdata/parsing-results/result-vis-excel-1.json'
result_path1 = 'src/validation/Gantt/testdata/parsing-results/result-vis-excel-2.json'
result_path2 = 'src/validation/Gantt/testdata/parsing-results/result-vis-excel-3.json'
result_path3 = 'src/validation/Gantt/testdata/parsing-results/result-vis-excel-4.json'

print("Validation Result of vis-excel-1")
print(validator.validate_visual(path,result_path))

print("Validation Result of vis-excel-2")
print(validator.validate_visual(path1,result_path1))

print("Validation Result of vis-excel-3")
print(validator.validate_visual(path2,result_path2))

print("Validation Result of vis-excel-4")
print(validator.validate_visual(path3,result_path3))
