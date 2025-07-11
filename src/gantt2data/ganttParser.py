import camelot
import json
import re
from pydantic import BaseModel
import pandas as pd

class Task(BaseModel):
    id: int | None = None
    task: str | None = None
    start: str | None = None
    finish: str | None = None
    duration: str | None = None

path = "examples/ganttDiagrams/commercial-building-construction-gantt-chart.pdf"
path1 = "examples/ganttDiagrams/GANTT CHART EXAMPLE.pdf"
path2 = "examples/FinancialDocuments/BoQExample.pdf"

def rename_columns(df, old_column_names):
    new_column_names = df.iloc[0].tolist()  
    column_mapping = dict(zip(old_column_names, new_column_names))
    df = df.rename(columns=column_mapping)
    df = df.drop(df.index[0]).reset_index(drop=True)
    return df

def clean_empty_strings(df):
    return df.replace('', None)

def preprocess_df_and_check_column_names(df):
    is_empty = False
    df = clean_empty_strings(df)
    df = df.dropna(how='all')
    df = df.dropna(axis='columns', how='all')
    if df.empty:
        print('Data Frame is empty!')
        is_empty = True
        return None, is_empty
    all_numeric = all(isinstance(col, (int, float)) for col in df.columns)
    is_sequential = list(df.columns) == list(range(len(df.columns)))
    print("COLUMNNAMES")
    print(list(df.columns))
    old_column_names = list(df.columns)
    if all_numeric and is_sequential:
         df = rename_columns(df, old_column_names)
    return df, is_empty

def match(column_name):
    patterns = {
        'id': r'^id$',
        'task': r'^(task|task name|activity|activity name)$',
        'start': r'^(start|start date)$',
        'finish': r'^(finish|end|end date)$',
        'duration': r'^duration$'
    }
    
    # Convert column name to lowercase for case-insensitive matching
    column_lower = column_name.lower().strip()
    
    # Check each pattern
    for property_name, pattern in patterns.items():
        if re.match(pattern, column_lower):
            return property_name
    
    return "no match found"

def match_column_names_with_task_properties(df):
    column_names = df.columns.tolist()
    column_order = [None] * len(column_names)
    found_matches = 0
    for i, name in enumerate(column_names):
        title = match(str(name))
        if title != "no match found":
            column_order[i] = {
                "generalized_title": title,
                "column_name": name  # This should be the actual column name in the DataFrame
            }
            found_matches += 1  # Fixed: was =+ instead of +=
    print("Column order:", column_order)
    print("DataFrame columns:", df.columns.tolist())
    return column_order, found_matches

def create_tasks(column_order, df):
    tasks = []
    print("DataFrame shape:", df.shape)
    print("DataFrame columns:", df.columns.tolist())
    print("Column order:", column_order)
    
    for index, row in df.iterrows():
        task_data = {}
        
        for col_info in column_order:
            if col_info is not None:  # Skip unmapped columns
                generalized_title = col_info["generalized_title"]
                column_name = col_info["column_name"]
                
                # Debug: Check if column exists
                if column_name not in df.columns:
                    print(f"Warning: Column '{column_name}' not found in DataFrame")
                    print(f"Available columns: {df.columns.tolist()}")
                    continue
                
                value = row[column_name]
                
                if pd.isna(value) or value == '':
                    value = None
                elif generalized_title == 'id' and value is not None:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = None
                
                task_data[generalized_title] = value
        
        try:
            task = Task(**task_data)
            tasks.append(task)
        except Exception as e:
            print(f"Error creating task for row {index}: {e}")
            continue
    return tasks

def parse_gantt_chart(path, chart_format): 
    if chart_format== "tabular":
        tables = camelot.read_pdf(path)
        df = tables[0].df
        print("Original DataFrame:")
        print(df.head())
        print("Original columns:", df.columns.tolist())
        processed_df, is_empty = preprocess_df_and_check_column_names(df)
        if is_empty:
            return {"Table Recognition": "failed"}
    
        print("Processed DataFrame:")
        print(processed_df.head())
        print("Processed columns:", processed_df.columns.tolist())

        column_order, found_matches = match_column_names_with_task_properties(processed_df)
        print("Found matches:", found_matches)

        ## Remove this
        ## add if found_matches < 3 -> ai_column_matching
        if all(value is None for value in column_order):
            print("No column matches found")
            print(processed_df.to_string())
            return {"This didn't work": "We need a diffrent approach"}
        ## to do: rethink a little bit the validations-> only tabular structures are inputed here
        ## implement ai column matching if regex fails
        tasks = create_tasks(column_order, processed_df)
        json_string = json.dumps([ob.__dict__ for ob in tasks])
        return json_string
    else:
        return {"Not implemented": "Yet"}


