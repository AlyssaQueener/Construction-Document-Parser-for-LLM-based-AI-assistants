import camelot
import json
import re
from pydantic import BaseModel
import pandas as pd
import src.gantt2data.ganttParser as parser
import pdfplumber
import pymupdf as pymupdf



path = "examples/ganttDiagrams/commercial-building-construction-gantt-chart.pdf"
path1 = "examples/ganttDiagrams/GANTT CHART EXAMPLE.pdf"
path2 = "gantChart.pdf"

with pdfplumber.open(path2) as pdf:
    first_page = pdf.pages[0]
    table = first_page.extract_table()
    df = pd.DataFrame(table[1:], columns=table[0])
    print(df)
    




chart_format = "visual"
print(parser.parse_gantt_chart(path2, chart_format))