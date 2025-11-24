from mistralai import Mistral
import base64

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-latest"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)

def call_mistral_timeline(path):
    message = create_message_for_timeline_extraction(path)
    chat_response = client.chat.complete(
        model = model,
        messages = message,
        response_format = {
            "type": "json_object",
        }
    )

    return chat_response.choices[0].message.content

def create_message_for_timeline_extraction(path):
    base64_image = encode_image(path)
    text = create_timeline_prompt()
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
Look at the image and return all the activities in following format, an array list of all the names of the activities :
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