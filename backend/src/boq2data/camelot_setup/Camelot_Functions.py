
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

