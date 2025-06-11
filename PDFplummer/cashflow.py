
#!/usr/bin/env python3
"""
Cash Flow PDF Parser using pdfplumber
Step-by-step guide to extract and parse cash flow data from PDF
"""


import pdfplumber
import pandas as pd
import re
from typing import Dict, List, Any

def parse_cashflow_pdf(pdf_path: "cashflow.pdf") -> Dict[str, Any]:
    """
    Parse cash flow PDF and extract structured data
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        Dict containing parsed cash flow data
    """
    
    # Step 1: Open and extract text from PDF
    with pdfplumber.open(pdf_path) as pdf:
        # Get first page (assuming single page document)
        page = pdf.pages[0]
        
        # Extract raw text
        raw_text = page.extract_text()
        print("Raw text extracted successfully")
        
        # Try to extract tables if they exist
        tables = page.extract_tables()
        print(f"Found {len(tables)} tables in PDF")
        
    # Step 2: Parse the text into sections
    parsed_data = {
        'organization': '',
        'year': '',
        'starting_cash': 0,
        'monthly_cash_flow': {},
        'income_sources': {},
        'expenses': {},
        'totals': {}
    }
    
    # Step 3: Extract basic information
    lines = raw_text.split('\n')
    
    for i, line in enumerate(lines):
        # Extract organization name
        if '[organization]' in line:
            parsed_data['organization'] = line.strip()
            
        # Extract year
        if 'For [year]' in line and 'CASH AVAILABLE JAN 1:' in line:
            # Extract starting cash amount
            cash_match = re.search(r'(\d+\.?\d*)', line.split('CASH AVAILABLE JAN 1:')[1])
            if cash_match:
                parsed_data['starting_cash'] = float(cash_match.group(1))
    
    # Step 4: Parse monthly cash flow data
    cash_flow_section = extract_cash_flow_section(raw_text)
    parsed_data['monthly_cash_flow'] = cash_flow_section
    
    # Step 5: Parse income sources
    income_section = extract_income_section(raw_text)
    parsed_data['income_sources'] = income_section
    
    # Step 6: Parse expenses
    expenses_section = extract_expenses_section(raw_text)
    parsed_data['expenses'] = expenses_section
    
    return parsed_data

def extract_cash_flow_section(text: str) -> Dict[str, List[float]]:
    """Extract monthly cash flow data"""
    cash_flow = {}
    lines = text.split('\n')
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for line in lines:
        if 'Newly Received' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 12:
                cash_flow['newly_received'] = values[:12]
                
        elif 'Carry Over' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 12:
                cash_flow['carry_over'] = values[:12]
                
        elif 'Total Cash' in line and 'CASH FLOW' not in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 12:
                cash_flow['total_cash'] = values[:12]
                
        elif 'Monthly Expense' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 12:
                cash_flow['monthly_expenses'] = values[:12]
                
        elif 'End of Month Cash Balance' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 12:
                cash_flow['end_month_balance'] = values[:12]
    
    return cash_flow

def extract_income_section(text: str) -> Dict[str, List[float]]:
    """Extract income sources data"""
    income = {}
    lines = text.split('\n')
    
    for line in lines:
        if 'Individual Donors' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 12:
                income['individual_donors'] = values[1:13]  # Skip first total
                
        elif 'Foundations' in line and 'Individual' not in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 2:
                income['foundations'] = pad_monthly_values(values[1:], 12)
                
        elif 'Contracts' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 2:
                income['contracts'] = pad_monthly_values(values[1:], 12)
    
    return income

def extract_expenses_section(text: str) -> Dict[str, Any]:
    """Extract expenses data"""
    expenses = {
        'salaries': {},
        'contractors': {},
        'program_expenses': {},
        'general_admin': {}
    }
    
    lines = text.split('\n')
    
    for line in lines:
        # Extract salary information
        if 'Executive Director' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 13:
                expenses['salaries']['executive_director'] = {
                    'annual': values[0],
                    'monthly': values[1:13]
                }
                
        # Add more salary parsing...
        elif '[Existing staff member]' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 13:
                expenses['salaries']['existing_staff'] = {
                    'annual': values[0],
                    'monthly': values[1:13]
                }
        
        # Extract contractor information
        elif 'Outside Accountant' in line:
            values = extract_numbers_from_line(line)
            if len(values) >= 13:
                expenses['contractors']['accountant'] = {
                    'annual': values[0],
                    'monthly': values[1:13]
                }
    
    return expenses

def extract_numbers_from_line(line: str) -> List[float]:
    """Extract all numbers from a line of text"""
    # Find all numbers (including decimals)
    numbers = re.findall(r'\d+\.?\d*', line)
    return [float(num) for num in numbers]

def pad_monthly_values(values: List[float], target_length: int) -> List[float]:
    """Pad monthly values list to target length with zeros"""
    result = [0.0] * target_length
    for i, val in enumerate(values[:target_length]):
        if i < len(values):
            result[i] = val
    return result

def create_dataframes(parsed_data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Convert parsed data to pandas DataFrames for analysis"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    dataframes = {}
    
    # Cash flow DataFrame
    if parsed_data['monthly_cash_flow']:
        cf_data = parsed_data['monthly_cash_flow']
        dataframes['cash_flow'] = pd.DataFrame(cf_data, index=months)
    
    # Income DataFrame
    if parsed_data['income_sources']:
        income_data = parsed_data['income_sources']
        dataframes['income'] = pd.DataFrame(income_data, index=months)
    
    return dataframes

def main():
    """
    Main function - Example usage
    """
    # Step 1: Install pdfplumber
    # pip install pdfplumber
    
    # Step 2: Parse the PDF
    pdf_path = "cashflow_1.pdf"  # Replace with your PDF path
    
    try:
        print("Starting PDF parsing...")
        parsed_data = parse_cashflow_pdf(pdf_path)
        
        print(f"Organization: {parsed_data['organization']}")
        print(f"Starting Cash: ${parsed_data['starting_cash']:,.2f}")
        
        # Step 3: Create DataFrames for analysis
        dataframes = create_dataframes(parsed_data)
        
        # Step 4: Display results
        if 'cash_flow' in dataframes:
            print("\nMonthly Cash Flow:")
            print(dataframes['cash_flow'])
            
        if 'income' in dataframes:
            print("\nIncome Sources:")
            print(dataframes['income'])
        
        # Step 5: Save to CSV
        for name, df in dataframes.items():
            csv_filename = f"cashflow_{name}.csv"
            df.to_csv(csv_filename)
            print(f"Saved {name} data to {csv_filename}")
            
    except FileNotFoundError:
        print(f"Error: Could not find PDF file '{pdf_path}'")
        print("Make sure the file path is correct")
        
    except Exception as e:
        print(f"Error parsing PDF: {str(e)}")
        print("Check if the PDF format matches expected structure")

if __name__ == "__main__":
    main()

# Additional utility functions for specific analysis

def analyze_cash_flow(dataframes: Dict[str, pd.DataFrame]) -> None:
    """Perform basic cash flow analysis"""
    if 'cash_flow' not in dataframes:
        print("No cash flow data available for analysis")
        return
        
    cf_df = dataframes['cash_flow']
    
    print("\n=== CASH FLOW ANALYSIS ===")
    
    # Minimum cash balance
    if 'end_month_balance' in cf_df.columns:
        min_balance = cf_df['end_month_balance'].min()
        min_month = cf_df['end_month_balance'].idxmin()
        print(f"Lowest cash balance: ${min_balance:,.2f} in {min_month}")
    
    # Average monthly expenses
    if 'monthly_expenses' in cf_df.columns:
        avg_expenses = cf_df['monthly_expenses'].mean()
        print(f"Average monthly expenses: ${avg_expenses:,.2f}")
    
    # Cash flow trend
    if 'end_month_balance' in cf_df.columns:
        start_balance = cf_df['end_month_balance'].iloc[0]
        end_balance = cf_df['end_month_balance'].iloc[-1]
        change = end_balance - start_balance
        print(f"Net change in cash: ${change:,.2f}")

def export_to_excel(dataframes: Dict[str, pd.DataFrame], filename: str = "cashflow_analysis.xlsx"):
    """Export all dataframes to Excel with multiple sheets"""
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name)
        print(f"Exported all data to {filename}")
    except ImportError:
        print("openpyxl not installed. Install with: pip install openpyxl")