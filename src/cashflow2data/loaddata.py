import pandas as pd
import json
import numpy as np

def parse_cashflow_csv(csv_file_path, output_json_path):
    """
    Parse cash flow CSV file and convert to structured JSON
    """
    
    # Read the CSV file with semicolon separator
    df = pd.read_csv(csv_file_path, sep=';', header=None)
    
    # Initialize the result dictionary
    result = {
        "organization": "",
        "year": "",
        "initial_cash": 0,
        "cash_flow_summary": {},
        "income": {},
        "expenses": {},
        "metadata": {}
    }
    
    # Convert all data to string for easier processing
    df = df.astype(str)
    
    print("Parsing CSV file...")
    print(f"CSV shape: {df.shape}")
    
    # Extract organization, year, and initial cash from first few rows
    for i in range(min(5, len(df))):
        row = df.iloc[i]
        
        # Look for initial cash amount
        for col_val in row:
            if "150.000" in str(col_val) or "CASH AVAILABLE JAN 1" in str(col_val):
                try:
                    # Extract the cash amount
                    cash_val = str(col_val).replace("CASH AVAILABLE JAN 1:", "").strip()
                    if cash_val.replace(".", "").replace(",", "").isdigit():
                        result["initial_cash"] = float(cash_val.replace(",", ""))
                except:
                    result["initial_cash"] = 150000  # Default from your data
                break
    
    # Define months for parsing
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Find and parse cash flow section
    print("Looking for CASH FLOW section...")
    for i, row in df.iterrows():
        first_col = str(row[0]).strip()
        
        if "CASH FLOW" in first_col:
            print(f"Found CASH FLOW at row {i}")
            
            # Initialize cash flow summary
            result["cash_flow_summary"] = {
                "newly_received": {},
                "carry_over": {},
                "total_cash": {},
                "monthly_expense": {},
                "end_of_month_balance": {}
            }
            
            # Parse the next several rows for cash flow data
            for j in range(i + 1, min(i + 8, len(df))):
                cash_row = df.iloc[j]
                row_label = str(cash_row[0]).strip()
                
                # Extract monthly values (columns 2-13 typically contain Jan-Dec)
                monthly_values = {}
                for k, month in enumerate(months):
                    try:
                        # Look for values in columns 2-13
                        if k + 2 < len(cash_row):
                            val = str(cash_row[k + 2]).strip()
                            if val not in ['nan', '', 'None'] and val.replace('.', '').replace(',', '').replace('-', '').isdigit():
                                monthly_values[month] = float(val.replace(',', ''))
                            else:
                                monthly_values[month] = 0
                    except:
                        monthly_values[month] = 0
                
                # Assign to appropriate category
                if "Newly Received" in row_label:
                    result["cash_flow_summary"]["newly_received"] = monthly_values
                elif "Carry Over" in row_label:
                    result["cash_flow_summary"]["carry_over"] = monthly_values
                elif "Total Cash" in row_label:
                    result["cash_flow_summary"]["total_cash"] = monthly_values
                elif "Monthly Expense" in row_label:
                    result["cash_flow_summary"]["monthly_expense"] = monthly_values
                elif "End of Month Cash Balance" in row_label:
                    result["cash_flow_summary"]["end_of_month_balance"] = monthly_values
            
            break
    
    # Find and parse income section
    print("Looking for INCOME section...")
    for i, row in df.iterrows():
        first_col = str(row[0]).strip()
        
        if "INCOME (Cash received)" in first_col:
            print(f"Found INCOME section at row {i}")
            
            result["income"] = {
                "individual_donors": {},
                "foundations": {},
                "contracts": {},
                "total": {}
            }
            
            # Parse income rows
            for j in range(i + 1, min(i + 15, len(df))):
                income_row = df.iloc[j]
                row_label = str(income_row[0]).strip()
                
                if row_label in ['', 'nan', 'None']:
                    continue
                
                # Extract monthly values
                monthly_values = {}
                for k, month in enumerate(months):
                    try:
                        if k + 2 < len(income_row):
                            val = str(income_row[k + 2]).strip()
                            if val not in ['nan', '', 'None'] and val.replace('.', '').replace(',', '').replace('-', '').isdigit():
                                monthly_values[month] = float(val.replace(',', ''))
                            else:
                                monthly_values[month] = 0
                    except:
                        monthly_values[month] = 0
                
                # Assign to appropriate category
                if "Individual Donors" in row_label:
                    result["income"]["individual_donors"] = monthly_values
                elif "Foundations" in row_label:
                    result["income"]["foundations"] = monthly_values
                elif "Contracts" in row_label:
                    result["income"]["contracts"] = monthly_values
                elif "TOTAL INCOME" in row_label:
                    result["income"]["total"] = monthly_values
            
            break
    
    # Find and parse expenses section
    print("Looking for EXPENSES section...")
    for i, row in df.iterrows():
        first_col = str(row[0]).strip()
        
        if "EXPENSES" in first_col and "Projected" in str(row[2]):
            print(f"Found EXPENSES section at row {i}")
            
            result["expenses"] = {
                "salaries": {},
                "contractors": {},
                "program_expenses": {},
                "general_admin": {},
                "total": {}
            }
            
            # Parse expenses rows - look for totals
            for j in range(i + 1, min(len(df) - 5, i + 50)):
                expense_row = df.iloc[j]
                row_label = str(expense_row[0]).strip()
                
                if row_label in ['', 'nan', 'None']:
                    continue
                
                # Extract monthly values
                monthly_values = {}
                for k, month in enumerate(months):
                    try:
                        if k + 2 < len(expense_row):
                            val = str(expense_row[k + 2]).strip()
                            if val not in ['nan', '', 'None'] and val.replace('.', '').replace(',', '').replace('-', '').isdigit():
                                monthly_values[month] = float(val.replace(',', ''))
                            else:
                                monthly_values[month] = 0
                    except:
                        monthly_values[month] = 0
                
                # Look for total rows
                if "Total Salary" in row_label:
                    result["expenses"]["salaries"] = monthly_values
                elif "Total Contractors" in row_label:
                    result["expenses"]["contractors"] = monthly_values
                elif "Total Program Expenses" in row_label:
                    result["expenses"]["program_expenses"] = monthly_values
                elif "Total G & A" in row_label:
                    result["expenses"]["general_admin"] = monthly_values
                elif "TOTAL EXPENSES" in row_label:
                    result["expenses"]["total"] = monthly_values
            
            break
    
    # Add metadata
    result["metadata"] = {
        "file_parsed": csv_file_path,
        "total_rows": len(df),
        "total_columns": len(df.columns)
    }
    
    # Save to JSON file
    with open(output_json_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Successfully parsed CSV and saved JSON to: {output_json_path}")
    
    # Print summary
    print("\nParsing Summary:")
    print(f"Initial Cash: {result['initial_cash']}")
    print(f"Cash Flow Summary sections: {len([k for k, v in result['cash_flow_summary'].items() if v])}")
    print(f"Income sections: {len([k for k, v in result['income'].items() if v])}")
    print(f"Expense sections: {len([k for k, v in result['expenses'].items() if v])}")
    
    return result

# Example usage with better error handling
if __name__ == "__main__":
    # Replace these paths with your actual file paths
    csv_file = "cashflow.csv"
    json_file = "cashflow_output1.json"
    
    try:
        print("Starting CSV parsing...")
        parsed_data = parse_cashflow_csv(csv_file, json_file)
        print("\n" + "="*50)
        print("PARSING COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"JSON file created: {json_file}")
        
        # Show a sample of the parsed data
        print("\nSample of parsed data:")
        if parsed_data["cash_flow_summary"]["total_cash"]:
            print("Total Cash for first few months:")
            for month, value in list(parsed_data["cash_flow_summary"]["total_cash"].items())[:3]:
                print(f"  {month}: {value}")
        
    except FileNotFoundError:
        print(f"ERROR: Could not find the file '{csv_file}'")
        print("Make sure the file exists in the same folder as this script.")
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure the CSV file is in the same folder as this script")
        print("2. Check that the filename is exactly correct (including spaces and special characters)")
        print("3. Make sure the file is not open in Excel or another program")