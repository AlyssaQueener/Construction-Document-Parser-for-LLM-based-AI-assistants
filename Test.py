from src.boq2data import extract_data
from src.boq2data.extract.loader import read_templates
from src.boq2data.output.format_boq import format_boq
import json

filename = "examples/FinancialDocuments/BOQ3.pdf"
templates = read_templates('examples/FinancialDocuments/templates')
result = extract_data(filename, templates=templates)
#structured_result = format_boq(result)
with open('testBoQ3.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4, ensure_ascii=False)