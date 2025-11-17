import json
from mistralai import Mistral

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)


def create_prompt_gantt(ground_truth, parser_result):
    """
    Evaluation prompt for title block extraction evaluation, llm as a judge
    """
    prompt = f"""
Floorplan Title Block Parser Evaluation

You are an expert evaluator assessing the performance of an automated parser that extracts activities from a gantt chart. Your task is to compare the parser's output against ground truth data and provide a quantitative evaluation.

Input Data
You will receive two JSON objects:
- Ground Truth: The correct gantt chart information
- Parser Output: The information extracted by the automated parser

Both contain a list of all the activities stated in the gantt chart. Each activiy follows following structure:
{{
        "id": int,
        "task": "string",
        "start": "string",
        "finish": "string",
        "duration": "string"
}}

Evaluation Methodology

Field-Level Matching Rules
For each field, determine the match quality:

Exact Match (1.0): Values are identical (case-insensitive, whitespace-normalized)
- Ground truth: "Project Approvals" → Parser: "Project Approvals" ✓
- Ground truth: "2018-09-27" → Parser: "2018-09-27" ✓

High Match (0.8): Minor formatting differences, but semantically identical
- Ground truth: "2018-09-27" → Parser: "27.09.2018" (date format conversion)


Partial Match (0.5): Significant differences but core information present


Low Match (0.3): Substantial discrepancy, minimal overlap


No Match (0.0): Completely incorrect or missing when ground truth exists
- Ground truth: "Design Phase" → Parser: "Reviewed by Stakeholders" ✗
- Ground truth: "2024-03-15" → Parser: null ✗

None Value Handling:
- Ground truth is None, Parser is None: Correct (1.0) - correctly identified no data
- Ground truth is None, Parser has value: False Positive (0.0) - hallucinated data
- Ground truth has value, Parser is None: False Negative (0.0) - missed data


Scoring Dimensions

1. Completeness Score (0-10)
Measures how many activities the parser successfully extracted.

Formula:
Completeness = (Correctly Extracted Activities/ Total Ground Truth Activities) × 10

Example:
- Ground truth has 10 activities
- Parser successfully extracts 8 activities
- Completeness = (8/10) × 10 = 8.0

2. Accuracy Score (0-10)
Measures the quality of extracted values across all fields.

Formula:
Accuracy = (Sum of all field match scores / Number of fields evaluated) × 10

Evaluate all fields of each activity.

Example:
- id: 1.0 (exact)
- task: 1.0 (exact)
- start: 0.5 (partial)
- finish: 0.8 (high)
- duration: 1.0 (exact)
- Accuracy = (4.3 / 5) × 10 = 8.6 → 8.6

3. Overall Score (0-10)
Formula:
Overall Score = (Completeness × 0.4) + (Accuracy × 0.6)

Accuracy is weighted higher because correct extraction is more valuable than just finding something.



Output Requirements
Return ONLY a valid JSON object with the following structure:

{{
    "completeness": "value",
    "accuracy": "value",
    "overall_score": "value",
}}


Ground Truth Data:
{ground_truth}

Parser Output Data:
{parser_result}

Begin your evaluation now. Return only the JSON output with no additional text.
"""
    return prompt


def read_json(path_to_json_file):
    with open(path_to_json_file) as json_data:
        df = json.load(json_data)
        json_data.close()
        return df

def call_mistral_evaluation(ground_truth, parser_result):
    message = create_prompt_gantt(ground_truth,parser_result)
    messages = [
        {
        "role": "user",
        "content": message
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

def llm_as_a_judge_titleblock(path_to_ground_truth, parsing_result):
    ground_truth = read_json(path_to_ground_truth)
    evaluation_result = call_mistral_evaluation(ground_truth,parsing_result)
    return evaluation_result