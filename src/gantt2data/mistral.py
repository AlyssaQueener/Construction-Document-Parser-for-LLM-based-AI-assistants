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
