import camelot
import json
import re
from pydantic import BaseModel
import pandas as pd
import src.gantt2data.mistral as mistral
import pymupdf as pymupdf
import pdfplumber
import src.gantt2data.ganttParserVisual as visual

class Task(BaseModel):
    id: int | None = None
    task: str | None = None
    start: str | None = None
    finish: str | None = None
    duration: str | None = None

### treshhold for ai fallback in tabular gantt parsing: ###
ai_fallback_treshhold = 3
def rename_columns(df: pd.DataFrame, old_column_names: list) -> pd.DataFrame :
    """
    Promotes the first row of a DataFrame to become the column headers.
    
    :param df: DataFrame whose first row contains the actual column names.
    :param old_column_names: Current (auto-generated) column names to be replaced.
    :return: DataFrame with renamed columns and the former header row removed.
    """
    new_column_names = df.iloc[0].tolist()  
    column_mapping = dict(zip(old_column_names, new_column_names))
    df = df.rename(columns=column_mapping)
    df = df.drop(df.index[0]).reset_index(drop=True)
    return df

def clean_empty_strings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces all empty strings in a DataFrame with None values.
    
    :param df: Input DataFrame potentially containing empty strings.
    :return: DataFrame with empty strings replaced by None.
    """
    return df.replace('', None)

def preprocess_df(df: pd.DataFrame) -> tuple[pd.DataFrame | None, bool]:
    """
    Cleans raw DataFrame containing gantt chart data by removing empty rows/columns and fixing column names.
    If DataFrame is empty, the camelot table extraction failed and thereby further parsing.
    
    For not empty data frames: if the columns are auto-generated sequential integers, the first
    data row is promoted to column headers.
    
    :param df: Raw DataFrame extracted from a PDF table.
    :return: Tuple of (processed DataFrame or None, bool indicating if the DataFrame was empty).
    """
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
    if all_numeric and is_sequential:
        old_column_names = list(df.columns)
        df = rename_columns(df, old_column_names)
    return df, is_empty

import re

def match(column_name:str) -> str:
    """
    Matches a single column name against known Gantt chart field patterns (supporting
    English and German terms) and returns the corresponding standardized property name.
    
    :param column_name: The column header string to match.
    :return: matched property or 'no match found'.
    """
    patterns = {
        'id': r'^(id|nr\.?|nummer)$',
        'task': r'^(task|task name|activity|activity name|vorgang|vorgangsname|aktivität|aufgabe)$',
        'start': r'^(start|start date|anfang)$',
        'finish': r'^(finish|end|end date|ende)$',
        'duration': r'^(duration|dauer)$'
    }

    column_lower = column_name.lower().strip()

    for property_name, pattern in patterns.items():
        if re.fullmatch(pattern, column_lower):
            return property_name

    return "no match found"


def match_column_names_with_task_properties(df: pd.DataFrame) -> tuple[list, int]:
    """
    Iterate over all DataFrame columns and attempt to map each one to a standardized
    Task property using regex matching to receive column order.
    
    :param df: preprocessed data frame containing gantt chart data
    :return: Tuple of (column_order list with mapping dicts or None per position,
             number of successfully matched columns).
    """
    column_names = df.columns.tolist()
    column_order = [None] * len(column_names)
    found_matches = 0
    for i, name in enumerate(column_names):
        title = match(str(name))
        if title != "no match found":
            column_order[i] = {
                "generalized_title": title,
                "column_name": name
            }
            found_matches += 1  
    return column_order, found_matches

def create_tasks(column_order: list, df: pd.DataFrame) -> list:
    """
    Converts DataFrame rows into a list of Task objects using the column name to property
    mapping.
    
    :param column_order: List of mapping dicts (or None) aligning DataFrame columns to Task fields.
    :param df: Processed DataFrame containing the Gantt chart data.
    :return: List of Task instances.
    """
    tasks = []
    
    for index, row in df.iterrows():
        task_data = {}
        
        for col_info in column_order:
            if col_info is not None:
                generalized_title = col_info["generalized_title"]
                column_name = col_info["column_name"]
                
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

#### MAIN FUNCTION ####
def parse_gantt_chart(path: str, chart_format: str) -> list: 
    """
    Parse gantt chart (pdf format) depending on chart layout (tabular/visual).
    Tabular: chart contains table containing activities and their respective data (start,end,id, etc.), bars only for visualization
    Visual: chart contains list of activtities, timeline and bars, bars are used to inferre start and end for each activtity 
    Full Ai: complex/ large gantt charts with visual layout
    
    :param path: File path to the Gantt chart PDF.
    :param chart_format: "tabular","visual", "full_ai"
    :return: JSON string of Task objects, or an error dict if table recognition failed.
    """
    if chart_format== "tabular":
        tables = camelot.read_pdf(path)
        df = tables[0].df
        processed_df, is_empty = preprocess_df(df)
        if is_empty:
            return {"Table Recognition": "failed"}
        column_order, found_matches = match_column_names_with_task_properties(processed_df)
        if found_matches < ai_fallback_treshhold:
            with pdfplumber.open(path) as pdf:
                print("Ai column name extraction")
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                column_order = json.loads(mistral.call_mistral_for_colums(text))
        tasks = create_tasks(column_order, processed_df)
        json_string = json.dumps([ob.__dict__ for ob in tasks],indent=4)
        return json_string
    elif(chart_format == "full_ai"):
        tasks = visual.parse_full_ai(path)
    else:
        tasks = visual.parse_gant_chart_visual(path)
        json_string = json.dumps([ob.__dict__ for ob in tasks], indent=4)
        return json_string