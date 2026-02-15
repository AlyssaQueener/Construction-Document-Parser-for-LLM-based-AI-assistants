import src.gantt2data.ganttParser as parser
import src.gantt2data.ganttParserVisual as parser_visual

## Example gantt chart pdfs with different layouts 
path_tabular = "examples/ganttDiagrams/commercial-building-construction-gantt-chart.pdf"
path_visual_hybrid = "src/validation/Gantt/testdata/test-vis-excel-1.pdf"
path_visual_ai = "src/validation/Gantt/testdata/test-visual-1.pdf"


## Parse gantt chart with tabular chart layout ##
result_tabular = parser.parse_gantt_chart(path_tabular, "tabular")
print(result_tabular)

## Parse gantt chart with visal layout using the hybrid pipeline
result_visual_hybrid = parser.parse_gantt_chart(path_visual_hybrid, "visual")
print(result_visual_hybrid)

## Parse gantt chart with visual layout using the ai driven pipeline
result_full_ai = parser.parse_gantt_chart(path_visual_ai, "full_ai")
print(result_full_ai)




