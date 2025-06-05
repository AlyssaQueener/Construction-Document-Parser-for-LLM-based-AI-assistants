from src.boq2data import extract_data
from src.boq2data.extract.loader import read_templates
from src.boq2data.output import to_json
import json

filename = "examples/FinancialDocuments/BoQExample.pdf"
templates = read_templates('examples/FinancialDocuments/templates')
result = extract_data(filename, templates=templates)

# POST-PROCESSING: Attach section to each item
tables = result.get("tables", [])
current_section = None
grouped_rows = []

for row in tables:
    if row.get("section"):
        current_section = row["section"]
    elif row.get("item_no"):  # Make sure it's a valid item line
        row["section"] = current_section
        grouped_rows.append(row)

# Replace the tables with cleaned, grouped rows
result["tables"] = grouped_rows

# Print and write result
print("result")
print(json.dumps(result, indent=4, ensure_ascii=False))  # Pretty print

# Save to JSON file
with open('test.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4, ensure_ascii=False)