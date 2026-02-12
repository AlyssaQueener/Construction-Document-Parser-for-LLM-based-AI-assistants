import camelot
import json
import pandas as pd
import json

def cam_extract(path, flav, pagenum):
    """
    Extract tables from PDF using Camelot with specified flavor.
    
    Args:
        path (str): Path to the PDF file
        flav (str): Extraction flavor ('stream', 'lattice', 'network', 'hybrid')
        pagenum (str): Page numbers to process (e.g., '1', '1-3', 'all')
    
    Returns:
        camelot.core.TableList: Extracted tables object
    """
    # Step 1: Read tables from the PDF
    tables = camelot.read_pdf(path, flavor=flav, pages=pagenum)
    print(f"Found {tables.n} tables")
    print(tables[0].parsing_report)
    return tables


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





# Note: Camelot's accuracy metric does not match expected output quality
# May need custom function to evaluate extraction quality
def cam_extract_accuracy(path, pagenum):
    """
    Test all Camelot extraction flavors and return the one with highest accuracy.
    
    Args:
        path (str): Path to the PDF file
        pagenum (str): Page numbers to process
    
    Returns:
        camelot.core.TableList: Tables extracted with best-performing flavor
    
    Note:
        Camelot's accuracy only measures text-assignment completeness,
        not table structure quality.
    """
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

def detect_column_headers(data):
    """
    Attempts to detect column headers from the first row or applies default BOQ column names.
    
    This function analyzes the first row of extracted table data to determine if it contains
    header information (by checking for common BOQ keywords). If headers are detected, they
    are used as column names; otherwise, standard BOQ column names are applied.
    
    Args:
        data (list[dict]): List of row dictionaries with numeric string keys (e.g., "0", "1", "2")
                          representing column indices. Each dict represents one table row.
    
    Returns:
        dict: Mapping from numeric string keys to column names.
              Format: {"0": "Item_Number", "1": "Description", ...}
              Returns empty dict if data is empty.
    
    Logic:
        1. Check first row for common BOQ header keywords
        2. If keywords found → use first row values as headers
        3. If no keywords → apply default BOQ column structure
        4. Fill any unnamed columns with "Column_N" pattern
    
    Examples:
        >>> data = [{"0": "Item No", "1": "Description", "2": "Unit"}]
        >>> detect_column_headers(data)
        {"0": "Item No", "1": "Description", "2": "Unit"}
        
        >>> data = [{"0": "1.1", "1": "Concrete work", "2": "m³"}]
        >>> detect_column_headers(data)
        {"0": "Item_Number", "1": "Description", "2": "Unit"}
    """
    # Handle empty data gracefully
    if not data:
        return {}
    
    # Extract first row for header detection
    first_row = data[0]
    
    # Convert first row values to lowercase for case-insensitive keyword matching
    first_row_values = [v.lower() for v in first_row.values() if v]
    
    # Define common BOQ header keywords to detect header rows
    header_keywords = [
        'item', 'description', 'unit', 'quantity', 'qty', 'rate', 
        'price', 'amount', 'total', 'number', 'no', 'pos'
    ]
    
    # Check if any header keywords appear in the first row
    has_headers = any(keyword in ' '.join(first_row_values) for keyword in header_keywords)
    
    if has_headers:
        # First row contains headers - use them as column names
        # Fill empty headers with generic "Column_N" names
        return {k: v if v else f"Column_{k}" for k, v in first_row.items()}
    else:
        # First row is data, not headers - apply default BOQ column structure
        num_columns = len(first_row)
        
        # Standard BOQ column layout (typical order in construction documents)
        default_names = [
            "Item_Number",      # Column 0: Position/item reference number
            "Description",      # Column 1: Work item description
            "Unit",             # Column 2: Unit of measurement (m³, m², pcs, etc.)
            "Quantity",         # Column 3: Quantity of units
            "Rate",             # Column 4: Unit price/rate
            "Amount"            # Column 5: Total amount (Quantity × Rate)
        ]
        
        # Extend default names if table has more columns than expected
        while len(default_names) < num_columns:
            default_names.append(f"Column_{len(default_names)}")
        
        # Create mapping from numeric string keys to column names
        return {str(i): default_names[i] for i in range(num_columns)}
    
def cam_stream_merge(tables):
    """
    Flatten and merge extracted tables, handling broken lines across rows.
    
    Merges continuation lines where only column "1" (description field)
    contains text, concatenating them with the previous row.
    
    Args:
        tables (camelot.core.TableList): Extracted tables from Camelot
    
    Returns:
        list[dict]: List of row dictionaries with merged continuation lines
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





#Execution of the code 
if __name__ == "__main__":
    
    import warnings
    warnings.filterwarnings('ignore')  # Suppress warnings
    
    path = 'examples/FinancialDocuments/BOQ4.pdf'
    page_num = 'all'
    
    # Since you know 'stream' works best, just use it directly
    flav = 'stream'
    tables_boq4 = cam_extract(path, flav, page_num)
    
    # Optional: Test accuracy if needed
    # cam_extract_accuracy(path, page_num)
    
    # Process tables
    tables_boq_processed = cam_stream_merge(tables_boq4)
    print(tables_boq_processed)