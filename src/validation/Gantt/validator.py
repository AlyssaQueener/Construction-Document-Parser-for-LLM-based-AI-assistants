import json
from mistralai import Mistral

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)

def create_prompt_gantt_new(ground_truth, parser_result):
    """
    Creates an evaluation prompt for Gantt chart parser assessment using LLM as a judge.
    Compares parser output against ground truth with field-level scoring.
    
    Args:
        ground_truth: JSON object containing correct Gantt chart activities
        parser_result: JSON object containing parser-extracted activities
    
    Returns:
        str: Formatted evaluation prompt
    """
    prompt = f"""You are an expert evaluator assessing an automated Gantt chart parser. Compare the parser's output against ground truth data and provide quantitative scores with field-level analysis.

# Data Structure

Each activity has these fields:
- id (int): Activity identifier
- task (string): Activity name/description
- start (string): Start date
- finish (string): End date
- duration (string): Activity duration

# Field Matching Criteria

Score each field using these rules:

**Exact Match (1.0)**: Identical values (case-insensitive, whitespace-normalized)
- "Project Approvals" = "Project Approvals" ✓
- "2018-09-27" = "2018-09-27" ✓

**High Match (0.8)**: Minor formatting differences, semantically identical
- "2018-09-27" vs "27.09.2018" (same date, different format)
- "Foundation Work" vs "foundation work" (case difference only)

**Partial Match (0.5)**: Core information present, but significant differences
- "Design and Planning Phase" vs "Design Phase"
- "2024-03-15" vs "2024-03" (missing day component)

**Low Match (0.3)**: Minimal overlap, substantial discrepancy
- "Foundation Work" vs "Foundation"
- Date values off by several days

**No Match (0.0)**: Completely incorrect or missing
- "Design Phase" vs "Construction Phase" ✗
- Ground truth has value, parser returns null ✗
- Ground truth is null, parser hallucinates a value ✗

**Correct Null (1.0)**: Both ground truth and parser are null/None

# Scoring Methodology

## 1. Completeness Score (0-10)
Measures extraction coverage.

**Formula**: (Number of Matched Activities / Total Ground Truth Activities) × 10

An activity is "matched" if it can be reasonably paired with a ground truth activity (even if fields aren't perfect).

**Example**: Ground truth has 12 activities, parser matches 10 → (10/12) × 10 = 8.33

## 2. Accuracy Score (0-10)
Measures field-level extraction quality across all matched activities.

**Formula**: (Sum of All Field Match Scores / Total Number of Fields Evaluated) × 10

**Process**:
1. For each matched activity, score all 5 fields (id, task, start, finish, duration)
2. Sum all field scores across all matched activities
3. Divide by total fields evaluated (5 × number of matched activities)
4. Multiply by 10

**Example**:
- Activity 1: id=1.0, task=1.0, start=0.8, finish=1.0, duration=0.5 → Sum=4.3
- Activity 2: id=1.0, task=0.8, start=1.0, finish=1.0, duration=1.0 → Sum=4.8
- Total: 9.1 / 10 fields = 0.91 → 0.91 × 10 = 9.1

## 3. Overall Score (0-10)
Weighted combination emphasizing accuracy.

**Formula**: (Completeness × 0.4) + (Accuracy × 0.6)

**Rationale**: Accurate extraction is more valuable than just detecting activities.

# Field-Level Evaluation

For each matched activity pair, provide:
- Activity identifier (from ground truth)
- Field-by-field scores with brief justification for non-exact matches
- Any notable discrepancies

# Output Format

Return ONLY this JSON structure (no markdown, no additional text):

{{
    "completeness": <float>,
    "accuracy": <float>,
    "overall_score": <float>,
    "field_evaluations": [
        {{
            "ground_truth_id": <int>,
            "parser_id": <int or null>,
            "field_scores": {{
                "id": <float>,
                "task": <float>,
                "start": <float>,
                "finish": <float>,
                "duration": <float>
            }},
            "notes": "<brief explanation of any non-exact matches>"
        }}
    ],
    "summary": {{
        "total_ground_truth_activities": <int>,
        "total_matched_activities": <int>,
        "total_fields_evaluated": <int>,
        "false_positives": <int>,
        "false_negatives": <int>
    }}
}}

# Ground Truth Data
{ground_truth}

# Parser Output Data
{parser_result}

Evaluate now. Return only valid JSON."""

    return prompt
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
    message = create_prompt_gantt_new(ground_truth,parser_result)
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
def call_mistral_evaluation_visual(ground_truth, parser_result):
    message = create_prompt_gantt_visual(ground_truth,parser_result)
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

def validate(path_to_ground_truth, path_parsing_result):
    ground_truth = read_json(path_to_ground_truth)
    parsing_result = read_json(path_parsing_result)
    evaluation_result = call_mistral_evaluation(ground_truth,parsing_result)
    return evaluation_result

def validate_visual(path_to_ground_truth, path_parsing_result):
    ground_truth = read_json(path_to_ground_truth)
    parsing_result = read_json(path_parsing_result)
    evaluation_result = call_mistral_evaluation_visual(ground_truth,parsing_result)
    return evaluation_result

def create_prompt_gantt_visual(ground_truth, parser_result):
    """
    Creates an evaluation prompt for Gantt chart parser assessment using LLM as a judge.
    Compares parser output against ground truth with field-level scoring.
    Handles variable field presence - activities may contain different subsets of fields.
    
    Args:
        ground_truth: JSON object containing correct Gantt chart activities
        parser_result: JSON object containing parser-extracted activities
    
    Returns:
        str: Formatted evaluation prompt
    """
    prompt = f"""You are an expert evaluator assessing an automated Gantt chart parser. Compare the parser's output against ground truth data and provide quantitative scores with field-level analysis.

# Data Structure

Activities may contain any subset of these fields:
- id (int): Activity identifier
- task (string): Activity name/description
- start (string): Start date
- finish (string): End date (may also be called "end")
- duration (string): Activity duration

**Important**: Not all activities have all fields. Only evaluate fields that are present in the ground truth. Do not penalize the parser for missing fields that don't exist in ground truth.

# Field Matching Criteria

Score each field using these rules:

**Exact Match (1.0)**: Identical values (case-insensitive, whitespace-normalized)
- "Project Approvals" = "Project Approvals" ✓
- "2018-09-27" = "2018-09-27" ✓

**High Match (0.8)**: Minor formatting differences, semantically identical
- "2018-09-27" vs "27.09.2018" (same date, different format)
- "Foundation Work" vs "foundation work" (case difference only)

**Partial Match (0.5)**: Core information present, but significant differences
- "Design and Planning Phase" vs "Design Phase"
- "2024-03-15" vs "2024-03" (missing day component)

**Low Match (0.3)**: Minimal overlap, substantial discrepancy
- "Foundation Work" vs "Foundation"
- Date values off by several days

**No Match (0.0)**: Completely incorrect or missing
- "Design Phase" vs "Construction Phase" ✗
- Ground truth has value, parser returns null ✗
- Ground truth is null, parser hallucinates a value ✗

**Correct Null (1.0)**: Both ground truth and parser are null/None for this field

**Field Not in Ground Truth**: Do NOT evaluate or count this field. If ground truth lacks a field but parser provides it, this is neither penalty nor bonus - simply ignore it.

# Scoring Methodology

## 1. Completeness Score (0-10)
Measures extraction coverage.

**Formula**: (Number of Matched Activities / Total Ground Truth Activities) × 10

An activity is "matched" if it can be reasonably paired with a ground truth activity (even if fields aren't perfect).

**Example**: Ground truth has 12 activities, parser matches 10 → (10/12) × 10 = 8.33

## 2. Accuracy Score (0-10)
Measures field-level extraction quality across all matched activities.

**Formula**: (Sum of All Field Match Scores / Total Number of Fields Evaluated) × 10

**Process**:
1. For each matched activity, identify which fields exist in ground truth
2. Score ONLY those fields that exist in ground truth (ignore extra fields parser may have added)
3. Sum all field scores across all matched activities
4. Divide by total fields evaluated (varies per activity based on which fields are present)
5. Multiply by 10

**Example with Variable Fields**:
- Activity 1 (has task, start, finish): task=1.0, start=0.8, finish=1.0 → Sum=2.8, Fields=3
- Activity 2 (has task, start only): task=0.8, start=1.0 → Sum=1.8, Fields=2
- Activity 3 (has id, task, start, finish, duration): All fields → Sum=4.5, Fields=5
- Total: 9.1 / 10 fields = 0.91 → 0.91 × 10 = 9.1

## 3. Overall Score (0-10)
Weighted combination emphasizing accuracy.

**Formula**: (Completeness × 0.4) + (Accuracy × 0.6)

**Rationale**: Accurate extraction is more valuable than just detecting activities.

# Field-Level Evaluation

For each matched activity pair, provide:
- Activity identifier (use index if no id field exists)
- Field-by-field scores ONLY for fields present in ground truth
- Brief justification for non-exact matches
- List which fields were evaluated for this activity

# Output Format

Return ONLY this JSON structure (no markdown, no additional text):

{{
    "completeness": <float>,
    "accuracy": <float>,
    "overall_score": <float>,
    "field_evaluations": [
        {{
            "ground_truth_id": <int or string identifier>,
            "parser_id": <int or string or null>,
            "fields_evaluated": [<list of field names evaluated for this activity>],
            "field_scores": {{
                "<field_name>": <float>,
                ...only fields present in ground truth...
            }},
            "notes": "<brief explanation of any non-exact matches>"
        }}
    ],
    "summary": {{
        "total_ground_truth_activities": <int>,
        "total_matched_activities": <int>,
        "total_fields_evaluated": <int>,
        "false_positives": <int>,
        "false_negatives": <int>,
        "common_fields": [<list of fields commonly present across activities>]
    }}
}}

# Ground Truth Data
{ground_truth}

# Parser Output Data
{parser_result}

Evaluate now. Return only valid JSON."""

    return prompt