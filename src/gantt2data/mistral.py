"""
Mistral API Integration for Gantt Chart Parsing

This module provides functions to interact with the Mistral AI API for extracting
structured data from Gantt chart images. It supports multiple extraction modes:
- Timeline extraction (time axis parsing)
- Activity/task extraction
- Column identification from raw text
- Full AI-driven activity + date extraction
- Chunk-based extraction for large charts

All vision-based functions encode images to base64 and send them alongside
carefully crafted prompts to Mistral's chat completion endpoint, requesting
JSON-formatted responses.
"""

from mistralai import Mistral
import base64

# ---------------------------------------------------------------------------
# Mistral client configuration
# ---------------------------------------------------------------------------
model = "mistral-small-2506"
api_key = "Your Api Key"  
client = Mistral(api_key=api_key)


def call_mistral_full_ai_parsing(path: str, option:str, activities:list, timeline:bool)->str:
    """Send gantt chart image to mistral for full ai parsing

    Args:
        path (str): File path to gantt chart image
        option (str): parsing strategy
        activities (list): List of activities contained in gantt chart
        timeline (bool): Bool for timeline presence

    Returns:
        Raw JSON string returned by the Mistral model.
    """
    message = create_message_for_full_ai_extraction(path, option, activities, timeline)
    chat_response = client.chat.complete(
        model=model,
        messages=message,
        response_format={
            "type": "json_object",  # Force structured JSON output
        }
    )
    return chat_response.choices[0].message.content


def call_mistral_timeline(path:str, option:str, activties:list)->str:
    """
    Send a Gantt chart image to Mistral and extract timeline or activity data
    depending on the chosen option.

    Args:
        path (str): File path to the Gantt chart image.
        option (str): Extraction mode – one of:
            - "check for timeline": Determine whether a timeline axis exists.
            - "badly extracted" / "no timeline": Parse the time axis values.
            - "full ai": Let the model extract both activities and dates.
            - "full ai w activities": Extract dates for a known activity list.
            - "chunks": Extract tasks/dates from a cropped chart chunk.
        activties (list[str] | None): Optional list of known activity names,
            used only with the "full ai w activities" option.

    Returns:
        str: Raw JSON string returned by the Mistral model.
    """
    message = create_message_for_timeline_extraction(path, option, activties)
    chat_response = client.chat.complete(
        model=model,
        messages=message,
        response_format={
            "type": "json_object",  # Force structured JSON output
        }
    )
    return chat_response.choices[0].message.content

def create_message_for_full_ai_extraction(path:str, option:str, activties:list|None, timeline: bool):
    """
    Build the multimodal (text + image) message payload for full ai parsing request.

    Selects the appropriate prompt text based on timeline parameter and activties,
    then pairs it with the base64-encoded chart image.

    Args:
        path (str): File path to the Gantt chart image.
        timeline (bool): timeline present (True|False).
        activties (list[str] | None): Known activities for guided extraction.

    Returns:
        list[dict]: A single-element list containing the user message with
            text and image content blocks, ready for the Mistral API.
    """
    base64_image = encode_image(path)

    # Select the prompt based on the requested extraction strategy
    if option == "full ai" and timeline:
        text = create_promt_full_ai()
    elif option == "full ai" and not timeline:
        text = create_promt_full_ai_no_timeline()
    elif option == "full ai w activities":
        text = create_message_ai_and_provided_activities(activties)
    elif option == "chunks" and timeline:
        text = create_message_for_chunks()
    elif option == "chunks" and not timeline:
        text = create_message_for_chunks_no_timeline()
    

    # Assemble multimodal message: text prompt + base64-encoded image
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                }
            ]
        }
    ]
    return messages


def create_message_for_timeline_extraction(path:str, option:str, activties:list):
    """
    Build the multimodal (text + image) message payload for timeline-related
    extraction requests.

    Selects the appropriate prompt text based on the extraction `option`,
    then pairs it with the base64-encoded chart image.

    Args:
        path (str): File path to the Gantt chart image.
        option (str): Extraction mode (see `call_mistral_timeline`).
        activties (list[str] | None): Known activities for guided extraction.

    Returns:
        list[dict]: A single-element list containing the user message with
            text and image content blocks, ready for the Mistral API.
    """
    base64_image = encode_image(path)

    # Select the prompt based on the requested extraction strategy
    if option == "check for timeline":
        text = create_message_for_check_for_timeline()
    if option == "badly extracted":
        text = create_timeline_prompt_new()
    if option == "no timeline":
        text = create_timeline_prompt_new()

    # Assemble multimodal message: text prompt + base64-encoded image
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                }
            ]
        }
    ]
    return messages


# ===========================================================================
# 2. ACTIVITY EXTRACTION
# ===========================================================================

def call_mistral_activities(path:str)->str:
    """
    Extract the list of activity/task names visible in a Gantt chart image.

    This function focuses only on identifying *what* activities exist (not
    their dates or durations). The returned JSON is a flat list of strings.

    Args:
        path (str): File path to the Gantt chart image.

    Returns:
        str: JSON string containing an array of activity names.
    """
    message = create_message_for_activity_extraction(path)
    chat_response = client.chat.complete(
        model=model,
        messages=message,
        response_format={
            "type": "json_object",
        }
    )
    return chat_response.choices[0].message.content


def create_message_for_activity_extraction(path:str)->list:
    """
    Build the multimodal message for activity-name extraction.

    Args:
        path (str): File path to the Gantt chart image.

    Returns:
        list[dict]: Mistral-compatible message list with text + image.
    """
    base64_image = encode_image(path)
    text = create_activities_prompt()
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                }
            ]
        }
    ]
    return messages


# ===========================================================================
# 3. COLUMN IDENTIFICATION (text-only, no image)
# ===========================================================================

def call_mistral_for_colums(text):
    """
    Identify standard Gantt chart columns (id, task, start, finish, duration)
    from raw text extracted via PDF parsing.

    Unlike the other functions this is a *text-only* call – no image is sent.
    Useful when a table has already been extracted from a PDF but the column
    semantics are unknown.

    Args:
        text (str): Raw text content extracted from a Gantt chart PDF.

    Returns:
        str: JSON string mapping detected columns to generalised titles.
    """
    message = create_column_identification_promt(text)
    messages = [
        {
            "role": "user",
            "content": message,
        }
    ]
    chat_response = client.chat.complete(
        model=model,
        messages=messages,
        response_format={
            "type": "json_object",
        }
    )
    return chat_response.choices[0].message.content


# ===========================================================================
# 4. IMAGE ENCODING UTILITY
# ===========================================================================

def encode_image(image_path:str):
    """
    Read an image file from disk and return its base64-encoded string.

    Args:
        image_path (str): Absolute or relative path to the image file.

    Returns:
        str | None: Base64-encoded UTF-8 string of the image, or None on error.
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


# ===========================================================================
# 5. PROMPT TEMPLATES
# ===========================================================================
# Each function below returns a carefully crafted prompt string for a
# specific extraction task. They are separated to keep concerns isolated
# and to allow easy iteration on individual prompts.


def create_activities_prompt():
    """
    Prompt for extracting the ordered list of activity names from a chart.

    The model is instructed to return a flat JSON array of strings (no wrapper
    object) so the result can be directly parsed downstream.
    """
    prompt = """
You are an expert in identifying the activities/ tasks which are listed in a gantt chart.
Look at the image and return all the activities stated in the gantt chart. Use the exact order in which the activities are listed, dont omit or hallucinate a activity.
Return activities in the following format:
** array list of all the names of the activities **
[ "name of the recognized activity exactly written like in chart", "name of the recognized activity exactly written like in chart"]
Please include the names of the activies/task exactly as they are spelled in the chart. Return them as a list, don't do something like { "actvities" : ["a","b"]} since i cannot handle any other format in my further application.
Return the answer in valid JSON.


"""
    return prompt


def create_column_identification_promt(text:str):
    """
    Prompt for mapping raw PDF-extracted column headers to the five canonical
    Gantt chart fields: id, task, start, finish, duration.

    The extracted `text` is injected at the end of the prompt so the model
    can analyse it in context.

    Args:
        text (str): Raw text content from a Gantt chart PDF.

    Returns:
        str: Complete prompt with the text appended.
    """
    promt = f"""
        # Gantt Chart Column Identification Prompt

You are a data analysis assistant specializing in identifying columns in Gantt charts. Your task is to analyze a list of column names from a parsed Gantt chart table and identify which columns correspond to standard Gantt chart properties.

## Input Format
You will receive the full text content extracted from a Gantt chart PDF. This text may include:
- Column headers
- Row data
- Other text elements from the chart
- Potentially messy or imperfectly parsed content

Your task is to identify the column structure and extract the column names from this raw text.

## Column Categories to Identify
You need to identify columns that represent these 5 standard Gantt chart properties:
- **id**: Task identifier, ID, or number
- **task**: Task name, activity name, or description
- **start**: Start date or beginning time
- **finish**: End date, finish date, or completion time
- **duration**: Duration, length, or time span

## Instructions
1. **First, identify the column headers** from the raw text (they are typically at the top or repeated throughout)
2. **Extract the column names** - look for patterns that indicate column headers
3. **Analyze each column name** to determine its purpose
4. **Consider variations** in naming conventions (e.g., "Task Name" vs "Activity" vs "Description")
5. **Look for common abbreviations** and synonyms
6. **Be flexible** with formatting (spaces, underscores, capitalization)
7. **Handle imperfect parsing** - text extraction may have introduced errors or spacing issues
8. **Consider domain-specific terminology** that might be used

## Output Format
Return ONLY a JSON array with the column mapping. Do not include any other text, explanations, or formatting.

**Critical formatting requirements:**
- Return ONLY the JSON array, nothing else
- Use `None` for positions where no match is found
- Maintain the exact order of the identified columns
- Use the exact column names as found in the text in "column_name"
- Only use these 5 generalized titles: "id", "task", "start", "finish", "duration"

Example output (return exactly this format):
```json
[
    {{"generalized_title": "id", "column_name": "Project ID"}},
    {{"generalized_title": "task", "column_name": "Task Description"}},
    {{"generalized_title": "start", "column_name": "Start Date"}},
    {{"generalized_title": "finish", "column_name": "End Date"}},
    {{"generalized_title": "duration", "column_name": "Days"}}
]
```

If no match is found for a column:
```json
[
    {{"generalized_title": "id", "column_name": "Project ID"}},
    None,
    {{"generalized_title": "start", "column_name": "Start Date"}},
    None,
    {{"generalized_title": "duration", "column_name": "Days"}}
]
```

## Example Variations to Consider
- ID columns: "ID", "Task ID", "Item #", "No.", "Number", "Reference"
- Task columns: "Task", "Activity", "Description", "Name", "Work Item", "Deliverable"
- Start columns: "Start", "Begin", "From", "Commence", "Start Date", "Begin Date"
- Finish columns: "End", "Finish", "Complete", "To", "End Date", "Completion Date"
- Duration columns: "Duration", "Length", "Days", "Hours", "Time", "Span", "Period"

## Raw Text from Gantt Chart:
{text}

Analyze this raw text, identify the column headers, and return ONLY the JSON array mapping as specified above.
    """
    return promt


def create_timeline_prompt_new():
    """
    Prompt for extracting individual time-axis tick values from a chart.

    The model identifies the smallest repeated time unit on the x-axis and
    returns each tick as an object with:
      - timestamp_value: the label of the smallest unit
      - additional_info: concatenated higher-level headers
      - index: 0-based left-to-right position

    Used when the initial PDF-based timeline extraction failed ("badly
    extracted") or when no tabular timeline data was found ("no timeline").
    """
    prompt = """
You are given an image of a Gantt chart.

1. Identify the smallest repeated time unit on the x-axis (for example: individual days, weeks, months, quarters, or years).
2. Treat that smallest repeated unit as "timestamp_value".
3. For each "timestamp_value", set "additional_info" to a string that concatenates all higher-level time headers that apply to that unit, separated by spaces, ordered from lowest to highest level. Use exactly the labels as written in the chart, without translating or normalizing.
4. Additionally, output an integer field "index" for each timestamp:
   - "index" MUST start at 0 for the leftmost (earliest) timestamp on the x-axis.
   - "index" MUST increase by exactly 1 when moving one step to the right on the x-axis.
   - Each timestamp must have a unique "index".

Examples of possible values (do NOT copy them, just follow the format):
- "Monday"
- "Monday October"
- "27 Monday October"
- "Week 3 2025"

Return ONLY a JSON array of objects with this exact schema, no wrapper object, no extra keys:

[
  {
    "timestamp_value": "27",
    "additional_info": "Monday October",
    "index": 4
  }
]

Additional rules:
- Do not include any tasks or bars, only time axis values.
- If the chart has multiple header rows (e.g., years, then months, then days):
  - Use the lowest row (e.g., days) as "timestamp_value".
  - Combine the headers above (e.g., month, year) into "additional_info".
- If there is no higher-level header, set "additional_info" to an empty string "".
- The response must be valid JSON.
- The root element MUST be a JSON array.
- Use double quotes for all keys and string values.
- Do not add comments, explanations, or any extra text.
- The only allowed keys are "timestamp_value", "additional_info", and "index".
"""
    return prompt


def create_promt_full_ai():
    """
    Prompt for fully AI-driven extraction of activities *and* their dates.


    Returns tasks as JSON objects with keys: task, start, finish.
    """
    prompt = """# Gantt Chart Activity Extraction Prompt

You are an AI parser specialized in extracting activity information from Gantt charts. Your task is to identify all activities along with their start and end dates from the provided chart image.

## Task Overview
Extract each activity with its corresponding start and end dates.

## Steps

1. **Identify the timeline structure**: Examine all time headers in the chart, which may be hierarchical (e.g., years containing months, months containing weeks, weeks containing days)

2. **Timeline timestamp format**: For each timestamp position on the timeline, construct the full timestamp using this exact structure:
   - Start with the **smallest unit** (the most granular time division shown)
   - If higher-level time headers exist above it, **concatenate them** to the smallest unit
   - Separate multiple levels with **spaces**
   - Order from **lowest to highest level** (e.g., "15 March 2024" not "2024 March 15")
   - Use **exactly the labels as written** in the chart - do not translate, normalize, or reformat them
   
   Examples of correct timestamp construction:
   - If the chart shows "Mon 15" under "March" under "2024": timestamp is "Mon 15 March 2024"
   - If the chart shows "Week 3" under "Q2" under "2024": timestamp is "Week 3 Q2 2024"
   - If the chart shows only "Jan | Feb | Mar": timestamps are "Jan", "Feb", "Mar"
   - If the chart shows "1" under "January": timestamp is "1 January"

3. **Match activities to timeline**: For each activity bar:
   - Identify where the bar **starts** on the horizontal axis
   - Identify where the bar **ends** on the horizontal axis
   - Determine the corresponding timestamp at the start position using the format above
   - Determine the corresponding timestamp at the end position using the format above

## Output Format
Provide the results as a JSON array with the following structure:

```json
[
    {
        "task": "Activity Name",
        "start": "Start Date",
        "finish": "End Date"
    },
    {
        "task": "Activity Name",
        "start": "Start Date",
        "finish": "End Date"
    }
]
```

**Important**: 
- Use the exact keys: `"task"`, `"start"`, `"finish"`
- Dates should follow the format as they appear in the timeline or labels
- The output must be valid JSON

## Important Guidelines
- Extract ALL activities visible in the chart
- Maintain the exact spelling and capitalization of activity names
- Ensure timeline timestamps follow the specified format precisely
- If the chart uses vertical orientation, apply the same principles horizontally

```
Now, please analyze the provided Gantt chart and extract all activities with their start and end dates."""
    return prompt

def create_promt_full_ai_no_timeline():
    """
    Prompt for fully AI-driven extraction of activities *and* their dates for charts where
    Dates are labelled directly on/near the bars → copy them verbatim.

    Returns tasks as JSON objects with keys: task, start, finish.
    """
    prompt = """# Gantt Chart Activity Extraction Prompt

You are an AI parser specialized in extracting activity information from Gantt charts. Your task is to identify all activities along with their start and end dates from the provided chart image.

## Task Overview
Extract each activity with its corresponding start and end dates.

Steps:
1. **Extract direct labels**: Look for date text that is:
   - Written on the bars themselves
   - Connected to bars with lines or arrows
   - Positioned immediately adjacent to the bar start/end points

2. **Record exactly as shown**: Copy the date labels exactly as they appear in the chart

## Output Format
Provide the results as a JSON array with the following structure:

```json
[
    {
        "task": "Activity Name",
        "start": "Start Date",
        "finish": "End Date"
    },
    {
        "task": "Activity Name",
        "start": "Start Date",
        "finish": "End Date"
    }
]
```

**Important**: 
- Use the exact keys: `"task"`, `"start"`, `"finish"`
- Dates should follow the format as they appear in the timeline or labels
- The output must be valid JSON


```
Now, please analyze the provided Gantt chart and extract all activities with their start and end dates."""
    return prompt


def create_message_ai_and_provided_activities(activities):
    """
    Prompt for date extraction when the activity list is already known.

    The pre-identified `activities` list is embedded in the prompt so the
    model can focus on matching bars to dates instead of also having to
    recognise activity names. If the model spots additional activities not
    in the list, it should still include them.

    Args:
        activities (list[str]): Known activity names to look for.

    Returns:
        str: Complete prompt with the activity list injected.
    """
    prompt = f"""# Gantt Chart Date Extraction

You are an AI parser extracting start and end dates from Gantt charts.

## Input
- A Gantt chart image
- Activity list (may be incomplete): {activities}

## Task
For each activity, identify the **start date** and **end date** by:

**For charts WITH a timeline axis:**
- Locate where each activity bar begins and ends on the timeline
- Read the corresponding dates from the timeline scale

**For charts WITHOUT a timeline axis:**
- Find date labels directly on or near each activity bar
- Dates may be on the bar, at its edges, or connected with lines/arrows

## Date Extraction Rules
1. Match activity names from the provided list
2. Copy dates **exactly as shown** (e.g., "01/03/2024", "Mar 18", "Week 3")
3. Do NOT convert or normalize formats
4. Start date = left/beginning of bar; End date = right/end of bar
5. If you find unlisted activities, include them with their dates

## Output Format
Return valid JSON:
```json
[
    {{
        "task": "Activity Name",
        "start": "Start Date",
        "finish": "End Date"
    }}
]
```

**Rules:**
- Use exact keys: `"task"`, `"start"`, `"finish"`
- If date is missing or unclear: use `null`
- Insert any discovered activities in the correct position

Analyze the chart and extract all dates."""
    return prompt


def create_message_for_check_for_timeline():
    """
    Prompt to classify a Gantt chart as having a timeline axis or not.

    Returns a simple boolean JSON: {"timeline_present": true/false}.
    This is typically the first call in the extraction pipeline to decide
    which downstream strategy to use.
    """
    prompt = """You are an expert at analyzing Gantt charts. Your task is to identify how dates are represented in the chart.

There are two possible formats:

**Format 1: Timeline Present**
- A continuous timeline is displayed at the top or bottom of the chart
- Bars align with this timeline to show duration

**Format 2: Dates on Bars**
- Dates are directly labeled on or adjacent to individual activity bars
- No separate timeline axis exists

Analyze the provided Gantt chart image and determine which format is used.

Return your answer as JSON in exactly this format:
{
    "timeline_present": true
}

Use `true` if Format 1 (timeline present), or `false` if Format 2 (dates on bars)."""

    return prompt


def create_message_for_chunks():
    """
    Prompt for extracting tasks and dates from a *cropped chunk* of a
    larger Gantt chart.

    Used when the chart is too large for a single API call and has been
    split into overlapping horizontal strips. Each chunk includes the
    timeline header so the model can still resolve dates.
    """
    prompt = f"""# Gantt Chart Chunk Date Extraction

You are an AI parser extracting tasks and dates from Gantt chart chunks.

## Input
A chunk of a Gantt chart image, including timeline.

## Task
Extract ALL visible activities with their start and end dates. Activities may continue into adjacent chunks.

- Read dates from where each bar begins/ends on the timeline axis


## Date Extraction Rules
1. Copy dates **exactly as shown** (e.g., "01/03/2024", "Mar 18", "Week 3")
2. Do NOT convert or normalize formats
3. Start date = left/beginning of bar; End date = right/end of bar
4. If date is unclear/partial: extract what's visible
5. If date is missing: use `null`
6. Maintain activity order as shown in chart

## Output Format
Return valid JSON:
```json
[
    {{
        "task": "Activity Name",
        "start": "Start Date",
        "finish": "End Date"
    }}
]
```

Use exact keys: `"task"`, `"start"`, `"finish"`

Extract all activities from this chunk."""
    return prompt



def create_message_for_chunks_no_timeline():
    """
    Prompt for extracting tasks and dates from a *cropped chunk* of a
    larger Gantt chart.

    Used when the chart is too large for a single API call and has been
    split into overlapping horizontal strips. Each chunk includes the
    timeline header so the model can still resolve dates.
    """
    prompt = f"""# Gantt Chart Chunk Date Extraction

You are an AI parser extracting tasks and dates from Gantt chart chunks.

## Input
A chunk of a Gantt chart image.

## Task
Extract ALL visible activities with their start and end dates. Activities may continue into adjacent chunks.

- Find date labels on or near activity bars (on bar, at edges, connected with lines/arrows, above/below)

## Date Extraction Rules
1. Copy dates **exactly as shown** (e.g., "01/03/2024", "Mar 18", "Week 3")
2. Do NOT convert or normalize formats
3. Start date = left/beginning of bar; End date = right/end of bar
4. If date is unclear/partial: extract what's visible
5. If date is missing: use `null`
6. Maintain activity order as shown in chart

## Output Format
Return valid JSON:
```json
[
    {{
        "task": "Activity Name",
        "start": "Start Date",
        "finish": "End Date"
    }}
]
```

Use exact keys: `"task"`, `"start"`, `"finish"`

Extract all activities from this chunk."""
    return prompt