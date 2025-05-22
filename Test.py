from src.boq2data import extract_data
from src.boq2data.extract.loader import read_templates

filename = "examples/FinancialDocuments/BoQExample.pdf"
templates = read_templates('examples/FinancialDocuments/templates')
result = extract_data(filename, templates=templates)
print(result)