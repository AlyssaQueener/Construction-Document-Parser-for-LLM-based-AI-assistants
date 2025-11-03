import camelot
import json
import re
from pydantic import BaseModel
import pandas as pd
import src.gantt2data.ganttParser as parser
import pdfplumber
import pymupdf as pymupdf
from src.plan2data.helper import convert_pdf2img
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np
import src.gantt2data.helper as helper
import src.gantt2data.mistral as mistral
import src.gantt2data.ganttParserVisual as visual_parser



path = "examples/ganttDiagrams/commercial-building-construction-gantt-chart.pdf"
path1 = "examples/ganttDiagrams/GANTT CHART EXAMPLE.pdf"
path2 = "gantChart.pdf"
path3 = "examples/ganttDiagrams/zn_Potenziale_entfalten_GanttChartExample-2-2.pdf"

def extract_activities(df):
        activities = []
        
        # Get the first column (assuming it contains activities)
        first_column = df.iloc[:, 0]

        
        
        for value in first_column:
            if value is not None and value != 'None':
                # Clean the activity name
                activity = str(value)
                activities.append(activity)
        
        activities = activities
        return activities
    
def extract_timeline_rows(df):
        ## TO DO validation checker-> the granularity counter should equal the amount of columns-1 (one column for where activities are listed) -> if that isn't achieved yet i might should loop thourgh more rows or AI 
        timeline_rows = []
        
        for row_idx in range(min(3, len(df))):
            row = df.iloc[row_idx]
            granularity_counter = 0
            time_stemps = {}
            
            
            for col_idx, value in enumerate(row):
                if value is not None and value != 'None':
                    value_str = str(value)
                    time_stemps[col_idx] = value_str
                    granularity_counter += 1
            if granularity_counter > 2:
                time_line_info = {
                    "time_stemps" : time_stemps,
                    "time_line_granularity" : granularity_counter
                }
                timeline_rows.append(time_line_info)
        
       
        return timeline_rows

def get_vertical_center(element):
    return (element['top'] + element['bottom']) / 2
    
    # Function to check if two elements are vertically aligned
def is_vertically_aligned(activity, rectangle, tolerance):
    activity_center = get_vertical_center(activity)
    rect_center = get_vertical_center(rectangle)
    return abs(activity_center - rect_center) <= tolerance
    
    # Function to check if rectangle is to the right of activity (for Gantt bars)
def is_rectangle_to_right(activity, rectangle, min_gap=10):
    return rectangle['x0'] >= activity['x1'] + min_gap

def localize_activities(activities):
    unfound_activities = 0
    activities_with_loc = []
    for activity in activities:
        activity_with_bbox = first_page.search(activity)
        if not activity_with_bbox:
            unfound_activities += 1
            continue
        activity_with_loc = {
            "text": activity_with_bbox[0]['text'],
            "x0": activity_with_bbox[0]['x0'],
            "top": activity_with_bbox[0]['top'],
            "x1": activity_with_bbox[0]['x1'],
            "bottom": activity_with_bbox[0]['bottom']
        }
        activities_with_loc.append(activity_with_loc)
    return activities_with_loc, unfound_activities

def localize_timestamps(timeline):
    unfound_timestamps = 0
    for timestamp in timeline:
        timestamp_with_bbox = first_page.search(str(timestamp['timestamp_value']))
        if not timestamp_with_bbox:
            unfound_timestamps += 1
            continue
        
        localization = {
            "text": timestamp_with_bbox[0]['text'],
            "x0": timestamp_with_bbox[0]['x0'],
            "top": timestamp_with_bbox[0]['top'],
            "x1": timestamp_with_bbox[0]['x1'],
            "bottom": timestamp_with_bbox[0]['bottom']
        }
        
        # Add localization to the timestamp entry
        timestamp['timestamp_location'] = localization
    
    return timeline, unfound_timestamps

def find_bars(rectangles, activities_with_loc,tolerance):
     # Create mapping of activities to rectangles
    activity_rectangles = {}
    
    for activity in activities_with_loc:
        matching_rectangles = []
        
        for rectangle in rectangles:
            if is_vertically_aligned(activity, rectangle, tolerance):
                if is_rectangle_to_right(activity, rectangle):
                    matching_rectangles.append(rectangle)
        
        
        activity_rectangles[activity['text']] = matching_rectangles
    return activity_rectangles

def is_horizontally_aligned(timestamp, rectangle, tolerance=5):
    """
    Check if a timestamp is horizontally aligned with a rectangle.
    """
    if 'timestamp_location' not in timestamp:
        return False
    
    location = timestamp['timestamp_location']
    timestamp_center_x = (location['x0'] + location['x1']) / 2
    rect_left = rectangle['x0']
    rect_right = rectangle['x1']
    
    # Check if timestamp is within or overlaps with rectangle horizontally
    return (rect_left - tolerance <= timestamp_center_x <= rect_right + tolerance)

def match_bars_with_timeline(gantt_chart_bars, timeline_with_localization):
    """
    Match activity bars with timeline timestamps to find start and end dates.
    For each activity, only saves the first and last matching timestamps.
    """
    activity_timestamps = {}
    
    for activity, matching_rectangles in gantt_chart_bars.items():
        matching_timestamps = []  # Initialize once per activity
        
        for timestamp in timeline_with_localization:
            for rectangle in matching_rectangles:
                if is_horizontally_aligned(timestamp, rectangle):
                    relevant_timestamp_info = {
                        'timestamp': timestamp['timestamp_value'],
                        'column_index': timestamp['column_index'],
                        'additional_info': timestamp['additional_info']
                    }
                    matching_timestamps.append(relevant_timestamp_info)
                    break  # Found a match for this timestamp, no need to check other rectangles
        
        activity_timestamps[activity] = matching_timestamps
    
    return activity_timestamps



def create_single_timeline(time_line_rows):
    """
    Create a unified timeline using the most granular row as base.
    Additional information from other rows is added based on column index ranges.
    """
    if not time_line_rows:
        return []
    
    most_granular_row = max(time_line_rows, key=lambda row: row['time_line_granularity'])
    
    unified_timeline = []
    
    for col_idx, timestamp_value in most_granular_row['time_stemps'].items():
        timeline_entry = {
            'timestamp_value': timestamp_value,
            'column_index': col_idx,
            'additional_info': {}
        }
        
        # Add information from other rows based on column index ranges
        for row_idx, row in enumerate(time_line_rows):
            # Skip the most granular row as it's already the primary
            if row['time_line_granularity'] == most_granular_row['time_line_granularity']:
                continue
            
            # Find which timestamp from this row applies to current column
            applicable_timestamp = find_applicable_timestamp(col_idx, row['time_stemps'])
            
            if applicable_timestamp:
                row_key = f"row_{row_idx + 1}_info"
                timeline_entry['additional_info'][row_key] = applicable_timestamp
        
        unified_timeline.append(timeline_entry)
    
    return unified_timeline

def find_applicable_timestamp(target_col_idx, row_timestamps):
    """
    Find which timestamp from a row applies to the target column index.
    Uses the timestamp from the closest lower or equal column index.
    """
    if not row_timestamps:
        return None
    
    sorted_col_indices = sorted(row_timestamps.keys())
    
    applicable_col_idx = None
    for col_idx in sorted_col_indices:
        if col_idx <= target_col_idx:
            applicable_col_idx = col_idx
        else:
            break
    
    return row_timestamps.get(applicable_col_idx) if applicable_col_idx is not None else None

def visualize_with_matplotlib(pdf_path, gantt_chart_bars, activities_with_loc):
    """
    Convert PDF page to image and overlay bounding boxes using matplotlib
    """
    # Convert PDF to image
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x scaling for better quality
    img_data = pix.tobytes("png")
    
    # Convert to PIL image then to numpy array
    from io import BytesIO
    img = Image.open(BytesIO(img_data))
    img_array = np.array(img)
    
    # Create matplotlib figure
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    ax.imshow(img_array)
    
    # Define colors for different activities
    colors = plt.cm.Set3(np.linspace(0, 1, len(gantt_chart_bars)))
    
    # Draw bounding boxes for activities (in green)
    for activity in activities_with_loc:
        rect = Rectangle((activity['x0']*2, activity['top']*2), 
                        (activity['x1'] - activity['x0'])*2, 
                        (activity['bottom'] - activity['top'])*2,
                        linewidth=2, edgecolor='green', facecolor='none', alpha=0.7)
        ax.add_patch(rect)
        ax.text(activity['x0']*2, activity['top']*2-10, activity['text'], 
                fontsize=8, color='green', weight='bold')
    
    # Draw bounding boxes for bars (different color for each activity)
    for i, (activity_name, rectangles) in enumerate(gantt_chart_bars.items()):
        color = colors[i]
        for rect_data in rectangles:
            rect = Rectangle((rect_data['x0']*2, rect_data['top']*2), 
                            (rect_data['x1'] - rect_data['x0'])*2, 
                            (rect_data['bottom'] - rect_data['top'])*2,
                            linewidth=2, edgecolor=color, facecolor=color, alpha=0.3)
            ax.add_patch(rect)
    
    ax.set_title('Gantt Chart with Bounding Boxes\n(Green: Activities, Colors: Bars)', fontsize=14)
    ax.axis('off')
    plt.tight_layout()
    plt.show()
    
    doc.close()

print(visual_parser.parse_gant_chart_visual(path1))
#print(parser.parse_gantt_chart(path2,"visual"))
#visual_parser.parse_gant_chart_visual(path1)
    
    



