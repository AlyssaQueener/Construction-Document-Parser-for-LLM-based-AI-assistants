import pdfplumber
import camelot
import json
import re
from pydantic import BaseModel
import pandas as pd

class Task(BaseModel):
    id: int | None
    task: str | None
    start: str | None
    finish: str | None
    duration: str | None

path = "examples/ganttDiagrams/commercial-building-construction-gantt-chart.pdf"
path1 = "examples/ganttDiagrams/GANTT CHART EXAMPLE.pdf"
path2 = "examples/FinancialDocuments/BoQExample.pdf"

# Open the PDF
pdf = pdfplumber.open(path)
page = pdf.pages[0]
#print(page.rects[0])
#print(page.extract_table())
#print(pdf.pages[0].extract_tables())

import pymupdf

doc = pymupdf.open(path)
page = doc[0]
#page.get_text("boxes") # open a document




## if df not empty -> get data from data frame 
## rename columns if column header are just 0 1 2 3 ...
## try to match column names with regex (task, TASK, Task) and get index
## if no matches ->check with ai which task properties are available and which property is on which index:
## eg: "id": {
##          "available": true,
##          "index": 1
##      }
## sort dataframe, return list of task
def rename_columns(df):
    new_column_names = df.iloc[0].tolist()  
    df.columns = new_column_names  
    df = df.drop(df.index[0]) 
    df = df.reset_index(drop=True)  

def clean_empty_strings(df):
    return df.replace('', None)

def preprocess_df_and_check_column_names(df):
    clean_empty_strings(df)
    if df.empty:
        print('Data Frame is empty!')
        return('Table wasnt properly regocnized, try sth else')
    df.dropna(how='all')
    df.dropna(axis='columns', how='all')
    all_numeric = all(isinstance(col, (int, float)) for col in df.columns)
    is_sequential = list(df.columns) == list(range(len(df.columns)))
    if all_numeric and is_sequential:
        rename_columns(df)
    return df
## input 

def match(column_name):
    patterns = {
        'id': r'^id$',
        'task': r'^task$',
        'start': r'^start$',
        'finish': r'^(finish|end)$',
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
    for i,name in enumerate(column_names):
        title = match(name)
        if title != "no match found":
            column_order[i] = {
                "generalized_title" : title,
                "column_name" : name
            }
    print(column_order)
    return column_order

def create_tasks(column_order, df):
    tasks = []
    for index, row in df.iterrows():
        task_data = {}
        
        for col_info in column_order:
            if col_info is not None:  # Skip unmapped columns
                generalized_title = col_info["generalized_title"]
                column_name = col_info["column_name"]
                
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

def parse_gantt_chart(path): 
    tables = camelot.read_pdf(path)
    df = tables[0].df
    processed_df = preprocess_df_and_check_column_names(df)
    if processed_df.empty:
        return "We need a diffrent approach!"
    column_order = match_column_names_with_task_properties(df)
    if all(value is None for value in column_order):
        return {"This didn't work":"We need a diffrent apporach!"}
    tasks = create_tasks(column_order, df)
    json_string = json.dumps([ob.__dict__ for ob in tasks])
    return(json_string)

print(parse_gantt_chart(path1))
#match_column_names_with_task_properties(df)








# pydantic -> model tasks (id, task, start, finish, duration)
# return list of tasks 