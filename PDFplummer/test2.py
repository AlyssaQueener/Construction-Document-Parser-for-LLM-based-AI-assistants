import pdfplumber
import json
import os

# Path to your PDF file
pdf_path = "cashflow.pdf"  # Change this to the correct filename

# Where to save the JSON (e.g., Desktop)
output_path = "C:/Users/HP/Desktop/output.json"

raw_tables = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            raw_tables.append(table)

# Save raw tables to JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(raw_tables, f, indent=2, ensure_ascii=False)

print("✅ JSON saved to:", output_path)
