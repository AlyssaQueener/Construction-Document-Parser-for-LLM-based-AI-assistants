import src.gantt2data.ganttParserVisual as parser

path = 'examples/ganttDiagrams/Timeline Softwarelab final-2.pdf'
path_1 = 'examples/ganttDiagrams/test_3_visual.pdf'
print(parser.parse_full_ai(path_1))