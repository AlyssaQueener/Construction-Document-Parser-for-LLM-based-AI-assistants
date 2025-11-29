
import camelot
import json
import json



def cam_extract(path,flav, pagenum):
    # Step 1: Read tables from the PDF
    tables = camelot.read_pdf(path, flavor=flav, pages=pagenum)
    print(f"Found {tables.n} tables")
    print(tables[0].parsing_report)
    return tables

# Sadly the results do not match the ouput maybe we have to write our own function to check for best output 
def cam_extract_accuracy(path, pagenum):
    flavours = ['stream', 'lattice','network','hybrid']
    best_accuracy = -1
    best_flavor = None
    best_tables = None

    for flavor in flavours: 
        tables = camelot.read_pdf(path, flavor=flavor, pages=pagenum)
        report = tables[0].parsing_report
        acc = report.get('accuracy', 0)
        print(flavor, acc)

        if acc > best_accuracy:
            best_accuracy = acc
            best_flavor = flavor
            best_tables = tables

    print(f"\n Best flavor: {best_flavor} with accuracy {best_accuracy}")
    return best_tables


#Step 2: Flatten tables into list of rows
# def cam_stream_merge(tables):
#     """
#     Merges tables from Camelot extraction and handles multi-line rows.
#     Returns data with meaningful column headers.
#     """
#     camelot.plot(tables[0], kind='grid').show()
#     data = []
#     for table in tables:
#         df = table.df  #pandas DataFrame
#         for _, row in df.iterrows():
#             # Convert each row to a dictionary with column indices as keys
#             data.append({str(i): str(row[i]).strip() for i in range(len(row))})
#     output = []
#     current_row = None
#     for row in data:
#         if row.get("0", ""):  # New main row
#             current_row = row.copy()
#             output.append(current_row)
#         elif row.get("1", "") and current_row:  # Continuation line
#             current_row["1"] += " " + row["1"]

#     # Print cleaned result
#     print(json.dumps(output, indent=2, ensure_ascii=False))

#     # Save the output list of dicts to a file
#     # with open('output.json', 'w', encoding='utf-8') as f:
#     #     json.dump(output, f, ensure_ascii=False, indent=2)
#     return output

def cam_stream_merge(tables):
    """
    Merges tables from Camelot extraction and handles multi-line rows.
    Returns data with meaningful column headers.
    """
    camelot.plot(tables[0], kind='grid').show()
    data = []
    
    for table in tables:
        df = table.df  # pandas DataFrame
        for _, row in df.iterrows():
            # Convert each row to a dictionary with column indices as keys
            data.append({str(i): str(row[i]).strip() for i in range(len(row))})
    
    # Merge multi-line rows
    output = []
    current_row = None
    for row in data:
        if row.get("0", ""):  # New main row
            current_row = row.copy()
            output.append(current_row)
        elif row.get("1", "") and current_row:  # Continuation line
            current_row["1"] += " " + row["1"]
    
    # Convert to meaningful column names
    # Detect column headers from first row or use defaults
    column_mapping = detect_column_headers(output)
    
    formatted_output = []
    for row in output:
        formatted_row = {}
        for num_key, col_name in column_mapping.items():
            formatted_row[col_name] = row.get(num_key, "")
        formatted_output.append(formatted_row)
    
    # Print cleaned result
    print(json.dumps(formatted_output, indent=2, ensure_ascii=False))
    
    return formatted_output


def detect_column_headers(data):
    """
    Attempts to detect column headers or uses defaults.
    Returns a mapping from numeric keys to column names.
    """
    if not data:
        return {}
    
    # Check if first row looks like headers
    first_row = data[0]
    first_row_values = [v.lower() for v in first_row.values() if v]
    
    # Common header keywords
    header_keywords = ['item', 'description', 'unit', 'quantity', 'qty', 'rate', 
                       'price', 'amount', 'total', 'number', 'no', 'pos']
    
    has_headers = any(keyword in ' '.join(first_row_values) for keyword in header_keywords)
    
    if has_headers:
        # Use first row as headers
        return {k: v if v else f"Column_{k}" for k, v in first_row.items()}
    else:
        # Use default BoQ column names
        num_columns = len(first_row)
        default_names = [
            "Item_Number",      # Column 0
            "Description",       # Column 1
            "Unit",             # Column 2
            "Quantity",         # Column 3
            "Rate",             # Column 4
            "Amount"            # Column 5
        ]
        
        # Extend if there are more columns
        while len(default_names) < num_columns:
            default_names.append(f"Column_{len(default_names)}")
        
        return {str(i): default_names[i] for i in range(num_columns)}
# def cam_dict(output):
#     tables = camelot.read_pdf(path, flavor='stream', pages=pages)
#     camelot.plot(tables[0], kind='grid').show()

#     # Merge all tables spanning multiple pages
#     full_df = pd.concat([t.df for t in tables], ignore_index=True)

#     # Convert merged DataFrame to list of row-dicts with index-keys
#     rows = []
#     for _, row in full_df.iterrows():
#         rows.append({str(i): str(row[i]).strip() for i in range(len(row))})

#     if not rows:
#         return []

#     # Use first row as header labels
#     headers = [rows[0][str(i)] for i in range(len(rows[0]))]

#     output = []
#     current = None
#     for row in rows[1:]:
#         if row.get("0", "").strip():  # New main row
#             current = {headers[i]: row.get(str(i), "") for i in range(len(headers))}
#             output.append(current)
#         else:
#             # Continuation line: append description field
#             if current:
#                 cont = row.get("1", "").strip()
#                 if cont:
#                     current[headers[1]] += " " + cont

#     # Save and print
#     print(json.dumps(output, indent=2, ensure_ascii=False))
#     with open('output.json', 'w', encoding='utf-8') as f:
#         json.dump(output, f, ensure_ascii=False, indent=2)

#     return output

################################



#Execution of the code 
if __name__ == "__main__":
    path = 'examples/FinancialDocuments/BoQExample.pdf'
    flav = 'hybrid'
    page_num = '1'
    tables_boq4 = cam_extract(path,flav,page_num)
    #tables = cam_extract_accuracy(path,page_num)
    
    tables_boq_processed = cam_stream_merge(tables_boq4)

