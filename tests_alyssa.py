import src.gantt2data.ganttParserVisual as parser

path = 'examples/ganttDiagrams/Timeline Softwarelab final-2.pdf'
path_1 = 'examples/ganttDiagrams/test_3_visual.pdf'
#print(parser.parse_from_chunks(path_1))
#print(parser.parse_only_ai(path_1))

path_2 = 'src/validation/Gantt/testdata/test-vis-excel-1.pdf'
path_3 = 'src/validation/Gantt/testdata/test-vis-excel-2.pdf'
path_4 = 'src/validation/Gantt/testdata/test-vis-excel-3.pdf'
path_5 = 'src/validation/Gantt/testdata/test-vis-excel-4.pdf'


#print("Parsing Result 1:")
#print(parser.parse_gant_chart_visual(path_2))
#print("Parsing Result 2:")
#print(parser.parse_gant_chart_visual(path_3))
#print("Parsing Result 3:")
#print(parser.parse_gant_chart_visual(path_4))
print("Parsing Result 5:")
print(parser.parse_gant_chart_visual(path_5))