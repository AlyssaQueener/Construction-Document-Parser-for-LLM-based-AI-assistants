import src.gantt2data.ganttParserVisual as parser

path = 'examples/ganttDiagrams/Timeline Softwarelab final-2.pdf'
print(parser.parse_gant_chart_visual(path))