from src.boq2data import extract_data
from src.boq2data.extract.loader import read_templates
from src.boq2data.output import to_json
import json

filename = "examples/FinancialDocuments/BoQExample.pdf"
templates = read_templates('examples/FinancialDocuments/templates')
result = extract_data(filename, templates=templates)
print("result")
print(result)
with open('test.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4, ensure_ascii=False)