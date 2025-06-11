#from src.boq2data import extract_data
#from src.boq2data.extract.loader import read_templates
#from src.boq2data.output.format_boq import format_boq
#import json

#filename = "examples/FinancialDocuments/BoQ4.pdf"
#templates = read_templates('examples/FinancialDocuments/templates')
#result = extract_data(filename, templates=templates)
#structured_result = format_boq(result)
#with open('test.json', 'w', encoding='utf-8') as f:
 #   json.dump(structured_result, f, indent=4, ensure_ascii=False)

# from src.boq2data import extract_data
# from src.boq2data.extract.loader import read_templates
# from src.boq2data.output import to_json
# import json

# filename = "examples/FinancialDocuments/BoQ4.pdf"
# templates = read_templates('examples/FinancialDocuments/templates')
# result = extract_data(filename, templates=templates)

# # Print and write result
# print("result")
# print(json.dumps(result, indent=4, ensure_ascii=False))  # Pretty print

# # Save to JSON file
# with open('test.json', 'w', encoding='utf-8') as f:
#     json.dump(result, f, indent=4, ensure_ascii=False)
#     print(" JSON saved to test.json")

# import camelot.io as camelot
# tables = camelot.read_pdf('examples/FinancialDocuments/BoQ4.pdf', flavor='stream', pages='1-end')
# print(tables)
# test_camelot.py
import camelot
tables = camelot.read_pdf('examples/FinancialDocuments/BoQExample.pdf', flavor='stream', pages='1')
print(f"Found {tables.n} tables")

for i, table in enumerate(tables, start=1):
    print(f"\n=== Table {i} ===")
    print(table.df)

tables.export('test.json', f='json')
tables.export('all_tables.csv', f='csv', compress=True)

