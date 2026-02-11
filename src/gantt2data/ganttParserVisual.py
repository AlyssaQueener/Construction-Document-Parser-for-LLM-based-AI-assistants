import json
from pydantic import BaseModel
import pandas as pd
import src.gantt2data.mistral as mistral
import pymupdf as pymupdf
import pdfplumber
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np
import src.gantt2data.helper as helper
from collections import Counter
import os


class Task_visual(BaseModel):
    task: str | None = None
    start: str | None = None
    finish: str | None = None

def extract_activities_for_full_ai(df):
    """
    Extracts the first six columns of a DataFrame for use in the full-AI parsing pipeline.
    This subset typically contains activity metadata (name, IDs, dates, etc.) needed by the AI model.

    :param df: DataFrame extracted from the Gantt chart PDF table.
    :return: DataFrame with only the first 6 columns, or None if extraction fails.
    """
    try:
        first_six_columns = df.iloc[:, :6]
        return first_six_columns
    except Exception as e:
        print("Activities couldn't be extracted from data frame:", e)
        return None


def extract_activities(df):
    """
    Extracts activity/task names from the first column of a DataFrame.
    Filters out None and 'None' string values.

    :param df: DataFrame extracted from the Gantt chart PDF table.
    :return: List of activity name strings, or None if extraction fails.
    """
    activities = []
    
    try:
        first_column = df.iloc[:, 0]

        for value in first_column:
            if value is not None and value != 'None':
                activity = str(value)
                activities.append(activity)
    
        activities = activities
        return activities
    except:
        print("Activities couldn't be extracted from data frame")
        return None
    
def extract_timeline_rows(df):
    """
    Scans the first 3 rows of a DataFrame to identify timeline header rows.
    A row is considered a timeline row if it contains more than 2 non-empty values,
    indicating it holds time labels (e.g. months, weeks, dates).

    :param df: DataFrame extracted from the Gantt chart PDF table.
    :return: List of dicts, each containing 'time_stemps' (column_index → value mapping)
             and 'time_line_granularity' (count of non-empty cells in that row).
    """
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
    """
    Computes the vertical center (y-coordinate midpoint) of a bounding box element.

    :param element: Dict with 'top' and 'bottom' keys representing vertical bounds.
    :return: Float representing the vertical center coordinate.
    """
    return (element['top'] + element['bottom']) / 2
    
def is_vertically_aligned(activity, rectangle, tolerance):
    """
    Checks whether an activity label and a rectangle (bar) are vertically aligned
    within a given tolerance, meaning they sit on approximately the same row.

    :param activity: Dict with bounding box keys ('top', 'bottom') for the activity text.
    :param rectangle: Dict with bounding box keys ('top', 'bottom') for a PDF rectangle.
    :param tolerance: Maximum allowed vertical distance between centers (in PDF points).
    :return: True if the vertical centers are within the tolerance.
    """
    activity_center = get_vertical_center(activity)
    rect_center = get_vertical_center(rectangle)
    return abs(activity_center - rect_center) <= tolerance
    
def is_rectangle_to_right(activity, rectangle, min_gap=10):
    """
    Checks whether a rectangle is positioned to the right of an activity label,
    with a minimum horizontal gap. This ensures the bar belongs to the chart area,
    not overlapping the activity text.

    :param activity: Dict with 'x1' (right edge of the activity text).
    :param rectangle: Dict with 'x0' (left edge of the rectangle).
    :param min_gap: Minimum horizontal distance in PDF points (default 10).
    :return: True if the rectangle starts at least min_gap pixels to the right of the activity.
    """
    return rectangle['x0'] >= activity['x1'] + min_gap

def localize_activities(activities, page):
    """
    Searches for each activity name string on the PDF page to obtain its
    bounding box coordinates. Uses pdfplumber's text search.

    :param activities: List of activity name strings to locate.
    :param page: pdfplumber Page object to search within.
    :return: Tuple of (list of activity dicts with bounding box info,
             count of activities that could not be found on the page).
    """
    unfound_activities = 0
    activities_with_loc = []
    for activity in activities:
        activity_with_bbox = page.search(activity)
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

def localize_timestamps(timeline, page):
    """
    Searches for each timestamp value on the PDF page and attaches the
    bounding box coordinates to the corresponding timeline entry in-place.

    :param timeline: List of timeline entry dicts, each containing 'timestamp_value'.
    :param page: pdfplumber Page object to search within.
    :return: Tuple of (timeline list with added 'timestamp_location' fields,
             count of timestamps that could not be found on the page).
    """
    unfound_timestamps = 0
    for timestamp in timeline:
        timestamp_with_bbox = page.search(str(timestamp['timestamp_value']))
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
        
        timestamp['timestamp_location'] = localization
    
    return timeline, unfound_timestamps

def find_bars(rectangles, activities_with_loc, tolerance):
    """
    Maps each localized activity to the PDF rectangles that are vertically aligned
    with it and positioned to its right. These rectangles represent the Gantt bars.

    :param rectangles: List of rectangle dicts from pdfplumber (page.rects).
    :param activities_with_loc: List of activity dicts with bounding box coordinates.
    :param tolerance: Vertical alignment tolerance in PDF points.
    :return: Dict mapping activity name → list of matching rectangle dicts.
    """
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
    Checks if a timestamp's horizontal center falls within a rectangle's
    horizontal span (with tolerance). Used to determine which time columns
    a Gantt bar spans.

    :param timestamp: Timeline entry dict with 'timestamp_location' containing bounding box.
    :param rectangle: Rectangle dict with 'x0' and 'x1' horizontal bounds.
    :param tolerance: Horizontal tolerance in PDF points (default 5).
    :return: True if the timestamp center is within the rectangle's horizontal range.
    """
    if 'timestamp_location' not in timestamp:
        return False
    
    location = timestamp['timestamp_location']
    timestamp_center_x = (location['x0'] + location['x1']) / 2
    rect_left = rectangle['x0']
    rect_right = rectangle['x1']
    
    return (rect_left - tolerance <= timestamp_center_x <= rect_right + tolerance)

def match_bars_with_timeline(gantt_chart_bars, timeline_with_localization, ai_extraction):
    """
    Correlates Gantt bars with timeline timestamps by checking horizontal alignment.
    For each activity, determines which timestamps its bar(s) overlap with.

    :param gantt_chart_bars: Dict mapping activity name → list of rectangle dicts.
    :param timeline_with_localization: List of timeline entry dicts with location info.
    :param ai_extraction: Boolean flag indicating if timeline was AI-extracted
                          (affects which key is used for column index).
    :return: Dict mapping activity name → list of matching timestamp info dicts.
    """
    activity_timestamps = {}
    
    for activity, matching_rectangles in gantt_chart_bars.items():
        matching_timestamps = []

        for timestamp in timeline_with_localization:
            for rectangle in matching_rectangles:
                if is_horizontally_aligned(timestamp, rectangle):
                    if ai_extraction == False:
                        relevant_timestamp_info = {
                            'timestamp': timestamp['timestamp_value'],
                            'column_index': timestamp['column_index'],
                            'additional_info': timestamp['additional_info']
                        }
                    if ai_extraction == True:
                        relevant_timestamp_info = {
                            'timestamp': timestamp['timestamp_value'],
                            'column_index': timestamp['index'],
                            'additional_info': timestamp['additional_info']
                        }
                    matching_timestamps.append(relevant_timestamp_info)
        
        activity_timestamps[activity] = matching_timestamps
    
    return activity_timestamps



def create_single_timeline(time_line_rows):
    """
    Merges multiple timeline header rows into one unified timeline. Uses the most
    granular row (most timestamps) as the base, then enriches each entry with
    contextual info from coarser rows (e.g. adding month labels to week-level entries).

    :param time_line_rows: List of timeline row dicts from extract_timeline_rows().
    :return: List of unified timeline entry dicts with 'timestamp_value',
             'column_index', and 'additional_info' from coarser rows.
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
        
        for row_idx, row in enumerate(time_line_rows):
            if row['time_line_granularity'] == most_granular_row['time_line_granularity']:
                continue
            
            applicable_timestamp = find_applicable_timestamp(col_idx, row['time_stemps'])
            
            if applicable_timestamp:
                row_key = f"row_{row_idx + 1}_info"
                timeline_entry['additional_info'][row_key] = applicable_timestamp
        
        unified_timeline.append(timeline_entry)
    
    return unified_timeline

def find_applicable_timestamp(target_col_idx, row_timestamps):
    """
    Finds which timestamp from a coarser timeline row applies to a given column index.
    Returns the value of the nearest timestamp at or before the target column,
    implementing a "carry-forward" logic (e.g. a month label applies to all its weeks).

    :param target_col_idx: Column index from the most granular timeline row.
    :param row_timestamps: Dict mapping column indices → timestamp values for a coarser row.
    :return: The applicable timestamp string, or None if no prior timestamp exists.
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
    Debug/visualization tool that renders the PDF page as an image and overlays
    colored bounding boxes for activities (green) and their matched Gantt bars
    (unique color per activity) using matplotlib.

    :param pdf_path: Path to the Gantt chart PDF file.
    :param gantt_chart_bars: Dict mapping activity name → list of matched rectangle dicts.
    :param activities_with_loc: List of activity dicts with bounding box coordinates.
    :return: None (displays a matplotlib plot).
    """
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
    img_data = pix.tobytes("png")
    
    from io import BytesIO
    img = Image.open(BytesIO(img_data))
    img_array = np.array(img)
    
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    ax.imshow(img_array)
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(gantt_chart_bars)))
    
    for activity in activities_with_loc:
        rect = Rectangle((activity['x0']*2, activity['top']*2), 
                        (activity['x1'] - activity['x0'])*2, 
                        (activity['bottom'] - activity['top'])*2,
                        linewidth=2, edgecolor='green', facecolor='none', alpha=0.7)
        ax.add_patch(rect)
        ax.text(activity['x0']*2, activity['top']*2-10, activity['text'], 
                fontsize=8, color='green', weight='bold')
    
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

def determine_start_end_of_activity(activity_timestamps):
    """
    Determines the start and end dates of each activity by finding the timestamps
    with the minimum and maximum column indices among its matched timestamps.

    :param activity_timestamps: Dict mapping activity name → list of timestamp info dicts
                                (each with 'timestamp', 'column_index', 'additional_info').
    :return: List of dicts with 'task', 'start', and 'finish' for each activity.
    """
    activities_with_dates = []
    for activity, timestamps in activity_timestamps.items():
        if timestamps:  
            min_timestamp = min(timestamps, key=lambda x: x['column_index'])
            max_timestamp = max(timestamps, key=lambda x: x['column_index'])
            start_date = str(min_timestamp['timestamp'] + " " + min_timestamp['additional_info'])
            end_date = str(max_timestamp['timestamp']+ " " + max_timestamp['additional_info'])
            activity_with_date = {
                "task" : activity,
                "start" : start_date,
                "finish": end_date
            }
            activities_with_dates.append(activity_with_date)

    return activities_with_dates

def check_bar_recognition(gantt_chart_bars):
    """
    Validates whether bar recognition was successful by analyzing the distribution
    of matched rectangle counts per activity. If >80% of activities have the same
    number of matched rectangles, it likely means background grid lines were detected
    instead of actual bars, indicating failure.

    :param gantt_chart_bars: Dict mapping activity name → list of matched rectangle dicts.
    :return: True if bar recognition seems valid, False if it likely failed.
    """
    print("GANTT CHART BARS:")
    total_bars = len(gantt_chart_bars)
    print(total_bars)
    bar_lengths = []
    for bar in gantt_chart_bars.values():
        print("length of matching rectangles")
        print(len(bar))
        bar_lengths.append(len(bar))
    counter = Counter(bar_lengths)
    print(counter)
    most_common_length, most_common_count = counter.most_common(1)[0]
    if most_common_count/total_bars > 0.8:
        print(most_common_count/total_bars)
        print("bar recognition failed")
        return False
    return True

def identify_bars_with_colours(gantt_chart_bars):
    """
    Fallback bar identification strategy that uses color analysis to filter out
    background rectangles (typically white/light gray) and retain only the
    actual colored Gantt bars.

    :param gantt_chart_bars: Dict mapping activity name → list of rectangle dicts (including color info).
    :return: Filtered dict with background-colored rectangles removed.
    """
    colors = extract_present_colours(gantt_chart_bars)
    filter_colors = analyze_colors(colors)
    color_filtered_gantt_chart_bars = filter_gantt_chart_bars(gantt_chart_bars, filter_colors)
    return color_filtered_gantt_chart_bars

def filter_gantt_chart_bars(gantt_chart_bars, filter_colors):
    """
    Removes rectangles whose fill color matches any of the filter colors
    (identified as background colors) from the activity-to-bar mapping.

    :param gantt_chart_bars: Dict mapping activity name → list of rectangle dicts.
    :param filter_colors: List of color tuples to exclude (background colors).
    :return: Filtered dict with background rectangles removed per activity.
    """
    color_filtered_gantt_chart_bars = {}
    for name_activity, rectangles in gantt_chart_bars.items():
        filtered_rects = []
        for rect in rectangles:
            if rect['non_stroking_color'] not in filter_colors:
                filtered_rects.append(rect)
        color_filtered_gantt_chart_bars[name_activity]= filtered_rects
    return color_filtered_gantt_chart_bars



def analyze_colors(colors):
    """
    Analyzes the color distribution across all matched rectangles and identifies
    very bright colors (likely white/light gray backgrounds) to be filtered out.
    Considers the top 3 most common colors as potential background candidates.

    :param colors: Dict mapping activity name → list of color tuples.
    :return: List of color tuples identified as background colors to filter.
    """
    all_colors = []
    for activity_colors in colors.values():
        all_colors.extend(activity_colors)
    
    color_counter = Counter(all_colors)
    total_rectangles = len(all_colors)
    
    print(f"Color frequency analysis:")
    for color, count in color_counter.most_common():
        percentage = (count / total_rectangles) * 100

    most_common_colors = color_counter.most_common(3)
    filter_colors = []
    for color in most_common_colors:
        if is_very_bright(color[0]):
            filter_color = color[0]
            filter_colors.append(filter_color)
    return filter_colors

def is_very_bright(color):
    """
    Determines if an RGB color tuple is very bright (all channels > 0.8),
    indicating it is likely a background color (white, light gray, etc.).

    :param color: Tuple of (R, G, B) values in the range [0, 1].
    :return: True if all color channels exceed 0.8.
    """
    if color[0]> 0.8 and color[1] > 0.8 and color[2] > 0.8:
        return True
    else:
        return False

def extract_present_colours(gantt_chart_bars):
    """
    Extracts the fill color ('non_stroking_color') from each rectangle
    for every activity, creating a color-per-activity mapping.

    :param gantt_chart_bars: Dict mapping activity name → list of rectangle dicts.
    :return: Dict mapping activity name → list of color tuples.
    """
    colours_of_bars = {}
    for name_activity, rectangles in gantt_chart_bars.items():
        colours = []
        for rect in rectangles:
            colours.append(rect['non_stroking_color'])
        colours_of_bars[name_activity]= colours
    return colours_of_bars

def parse_gant_chart_visual(path):
    """
    Main entry point for visually parsing a Gantt chart PDF. Orchestrates the full
    pipeline: extract table data, identify activities and timeline, locate them on
    the PDF page, match bars to activities, correlate bars with timestamps, and
    determine start/end dates. Falls back to Mistral AI when extraction quality
    is insufficient (too few activities, timestamps, or failed bar recognition).

    :param path: File path to the Gantt chart PDF.
    :return: List of dicts with 'task', 'start', 'finish' for each parsed activity.
    """
    tolerance = 2
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        image_path = helper.convert_pdf2img(path)
        tables = page.extract_table()
        boxes = page.rects
        df = pd.DataFrame(tables[1:], columns=tables[0])
        df = df.replace('', None)
        df = df.dropna(how='all')
        df = df.dropna(axis='columns', how='all')
        activities = extract_activities(df)
        row_count = len(df.index)
        if activities == None:
            activities = json.loads(mistral.call_mistral_activities(image_path))
        elif len(activities)< row_count - 5:
            activities = json.loads(mistral.call_mistral_activities(image_path))
        time_line_rows= extract_timeline_rows(df)
        timeline = create_single_timeline(time_line_rows)
        column_count = len(df.columns)
        ai_extraction = False
        if len(timeline) < column_count-5 or len(timeline) < 4:
             timeline = json.loads(mistral.call_mistral_timeline(image_path,"no timeline", None))
             ai_extraction = True
        time_line_with_localization, unfound_timestamps = localize_timestamps(timeline, page)
        if unfound_timestamps > len(timeline) - tolerance and ai_extraction== False:
            timeline = json.loads(mistral.call_mistral_timeline(image_path, "badly extracted", None))
            time_line_with_localization, unfound_timestamps = localize_timestamps(timeline, page)
        activities_with_loc, unfound_activites = localize_activities(activities, page)
        if unfound_activites > len(activities)-tolerance:
            activities = json.loads(mistral.call_mistral_activities(image_path))
            activities_with_loc, unfound_activites = localize_activities(activities, page)
        gantt_chart_bars = find_bars(boxes, activities_with_loc,2)
        success = check_bar_recognition(gantt_chart_bars)
        if not success:
            gantt_chart_bars = identify_bars_with_colours(gantt_chart_bars)
        activity_timestamps = match_bars_with_timeline(gantt_chart_bars,time_line_with_localization, ai_extraction)
        activities_with_dates = determine_start_end_of_activity(activity_timestamps)
        return activities_with_dates


def parse_full_ai(path):
    """
    Fully AI-driven parsing pipeline for complex Gantt charts. Checks for timeline
    presence via Mistral, extracts table data, and delegates to AI for interpretation.
    If the image is too large, it splits it into chunks for processing. Cleans up
    temporary image files after processing.

    :param path: File path to the Gantt chart PDF.
    :return: AI-parsed result (typically JSON string of activities with dates).
    """
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        image_path = helper.convert_pdf2img(path)
        check_for_timeline = json.loads(mistral.call_mistral_timeline(image_path, "check for timeline", None))
        if check_for_timeline['timeline_present'] == True:
            option = "w timeline"
        tables = page.extract_table()
        df = pd.DataFrame(tables[1:], columns=tables[0])
        df = df.replace('', None)
        df = df.dropna(how='all')
        df = df.dropna(axis='columns', how='all')
        activities = extract_activities_for_full_ai(df)
        print(activities)
        timeline = extract_timeline_rows(df)
        print(timeline)
        if len(activities) != 0:
            result=  mistral.call_mistral_timeline(image_path, "full ai w activities", activities)
        elif to_be_chunked(image_path):
            result= parse_from_chunks(path,option)
        else:
            result =  mistral.call_mistral_timeline(image_path, "full ai", None)
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"Deleted: {image_path}")
        except Exception as e:
            print(f"Warning: Could not delete {image_path}: {e}")
        return result


def extract_gantt_chart_from_chunks(chunked_chart):
    """
    Processes a list of image chunks through Mistral AI, parses each chunk's JSON
    response, and aggregates the results into a single list. Cleans up all temporary
    chunk image files afterward (even on failure).

    :param chunked_chart: List of file paths to image chunk files.
    :return: Combined list of parsed activity dicts from all chunks.
    """
    parsed_chart = []
    
    try:
        for image_path in chunked_chart:
            chart_json = mistral.call_mistral_timeline(image_path, "chunks", None)
            try:
                chart_part = json.loads(chart_json)
                parsed_chart.extend(chart_part)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse JSON from {image_path}: {e}")
                print(f"Raw response: {chart_json}")
                continue
    finally:
        for image_path in chunked_chart:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"Deleted: {image_path}")
            except Exception as e:
                print(f"Warning: Could not delete {image_path}: {e}")
    
    return parsed_chart
     
def parse_from_chunks(path, option):
    """
    Splits a Gantt chart PDF into smaller image chunks and parses each chunk
    separately via AI. Handles both timeline-preserving and regular splitting modes.

    :param path: File path to the Gantt chart PDF.
    :param option: "w timeline" to preserve timeline header in each chunk, or other for basic splitting.
    :return: Combined list of parsed activity dicts from all chunks.
    """
    if option == "w timeline":
        chart_chunks = helper.pdf_to_split_images_with_timeline(path,0)
    else:
        chart_chunks = helper.pdf_to_split_images(path,0)
    parsed_chart = extract_gantt_chart_from_chunks(chart_chunks)
    return parsed_chart
    
def to_be_chunked(image_path):
    """
    Determines if an image exceeds size thresholds and needs to be split into
    smaller chunks for AI processing. Checks against maximum dimension (1700px)
    and maximum total pixel area (2,890,000 px).

    :param image_path: File path to the image to evaluate.
    :return: True if the image exceeds any size threshold, False otherwise.
    """
    from PIL import Image
    max_dimension=1700
    max_area_pixels=2_890_000
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            total_pixels = width * height
            
        if width > max_dimension:
            return True
            
        if height > max_dimension:
            return True
            
        if total_pixels > max_area_pixels:
            return True
        return False
    except:
        print("could not measure image")
        return False