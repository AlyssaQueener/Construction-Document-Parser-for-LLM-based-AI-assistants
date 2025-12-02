from mistralai import Mistral
import base64

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-latest"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)

def call_mistral_timeline(path, option, activties):
    message = create_message_for_timeline_extraction(path, option, activties)
    chat_response = client.chat.complete(
        model = model,
        messages = message,
        response_format = {
            "type": "json_object",
        }
    )

    return chat_response.choices[0].message.content

def create_message_for_timeline_extraction(path, option, activties):
    base64_image = encode_image(path)
    if option == "check for timeline":
        text = create_message_for_check_for_timeline()
    if option == "badly extracted":
        text = create_timeline_prompt_new()
    if option == "no timeline":
        text = create_timeline_prompt_new()
    if option == "full ai":
        text = create_promt_full_ai()
    if option == "full ai w activities":
        text = create_message_ai_and_provided_activities(activties)
    if option == "chunks":
        text = create_message_for_chunks()
    
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

def create_timeline_prompt():
    prompt = """
You are an expert in identifying the timeline and timestemps which are used in a gantt chart.
Timestamps are supposed to be the smallest time unit on the chart, enabling somebody reading the chart to identify start and end date of a task.
Look at the image and return all the timestemps in following format :
[ 
    {
        'timestamp_value': "this value could be a date, the name of a month or somenthing like Q2, 1, etc.",
        'column_index': "index of the column in wich timestamp is located",
        'additional_info': "if there any additional info for the timestemps, e.g. a hierachically higher and more generall timerow add the information here"
    },
    {
        'timestamp_value': "this value could be a date, the name of a month or somenthing like Q2, 1, etc.",
        'column_index': col_idx,
        'additional_info': { }
    }
]
Please include the names of the timestamps exactly as they are spelled in the chart.
Dont do something like {'timestamps': [{'timestamp_value': 'Year 1', 'column_index': 0, 'additional_info': 'Yearly timestamp'}, {'timestamp_value': 'Q1', 'column_index': 1, 'additional_info': 'Quarterly timestamp within Year 1'}, {'timestamp_value': 'Q2', 'column_index': 2, 'additional_info': 'Quarterly timestamp within Year 1'}, {'timestamp_value': 'Q3', 'column_index': 3, 'additional_info': 'Quarterly timestamp within Year 1'},
But really only return the array of objects otherwise my further application doesn't work.
The response has to be in exactly the same format as specified above to ensure my further application works. 
Return the answer in valid JSON.


"""
    return prompt


def call_mistral_activities(path):
    message = create_message_for_activity_extraction(path)
    chat_response = client.chat.complete(
        model = model,
        messages = message,
        response_format = {
            "type": "json_object",
        }
    )

    return chat_response.choices[0].message.content

def create_message_for_activity_extraction(path):
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

def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:  # Added general exception handling
        print(f"Error: {e}")
        return None
def create_activities_prompt():
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

def call_mistral_for_colums(text):
    message = create_column_identification_promt(text)
    messages = [
        {
        "role": "user",
        "content": message,
        }
    ]
    chat_response = client.chat.complete(
        model = model,
        messages = messages,
        response_format = {
            "type": "json_object",
        }
    )
    response = chat_response.choices[0].message.content
    return response

def create_column_identification_promt(text):
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
    prompt = """# Gantt Chart Activity Extraction Prompt

You are an AI parser specialized in extracting activity information from Gantt charts. Your task is to identify all activities along with their start and end dates from the provided chart image.

## Task Overview
Extract each activity with its corresponding start and end dates. The chart may present dates in one of two scenarios:

## Scenario 1: Chart with Timeline
When a timeline is present at the top or bottom of the chart:

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

## Scenario 2: Dates Attached to Bars
When dates are directly labeled on or near the activity bars:

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

## Important Guidelines
- Extract ALL activities visible in the chart
- Maintain the exact spelling and capitalization of activity names
- For Scenario 1, ensure timeline timestamps follow the specified format precisely
- If a date is unclear or ambiguous, note this in your output
- If both scenarios appear to be present, prioritize directly attached dates (Scenario 2)
- Preserve any special characters or formatting in activity names
- If the chart uses vertical orientation, apply the same principles horizontally

```
Now, please analyze the provided Gantt chart and extract all activities with their start and end dates."""
    return prompt


def create_message_ai_and_provided_activities(activities):
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
    prompt = f"""# Gantt Chart Chunk Date Extraction

You are an AI parser extracting tasks and dates from Gantt chart chunks.

## Input
A chunk of a Gantt chart image. If a timeline is present, it will be included in the chunk.

## Task
Extract ALL visible activities with their start and end dates. Activities may continue into adjacent chunks.

**For charts WITH a timeline:**
- Read dates from where each bar begins/ends on the timeline axis

**For charts WITHOUT a timeline:**
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