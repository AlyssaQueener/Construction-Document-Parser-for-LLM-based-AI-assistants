import camelot
import json
import re
from pydantic import BaseModel
import pandas as pd
import src.gantt2data.ganttParser as parser

path = "examples/ganttDiagrams/commercial-building-construction-gantt-chart.pdf"
path1 = "examples/ganttDiagrams/GANTT CHART EXAMPLE.pdf"
path2 = "examples/FinancialDocuments/BoQExample.pdf"

print(parser.parse_gantt_chart(path))