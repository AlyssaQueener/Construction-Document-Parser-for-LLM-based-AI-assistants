import json
from mistralai import Mistral

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)
def create_prompt_titleblock(ground_truth, parser_result):
    """
    Evaluation prompt for title block extraction evaluation, llm as a judge
    """
    prompt = f"""
 Floorplan Title Block Parser Evaluation
You are an expert evaluator assessing the performance of an automated parser that extracts title block information from architectural floorplans. Your task is to compare the parser's output against ground truth data and provide a quantitative evaluation.
Input Data
You will receive two JSON objects:

Ground Truth: The correct title block information
Parser Output: The information extracted by the automated parser

Both contain the following fields:

client
creation_date
drawing_name
project_name
location
scale
architect
confidence (parser output only)

Evaluation Methodology
Field-Level Matching Rules
For each field, determine the match quality:
Exact Match (1.0): Values are identical (case-insensitive, whitespace-normalized)

Ground truth: "Max Mustermann" → Parser: "Max Mustermann" ✓
Ground truth: "1:100" → Parser: "1:100" ✓

High Match (0.8): Minor formatting differences, but semantically identical

Ground truth: "15.03.2024" → Parser: "2024-03-15" (date format conversion)
Ground truth: "M 1:100" → Parser: "1:100" (notation difference)
Ground truth: "Schmidt & Partner" → Parser: "Schmidt & Partner GmbH" (added suffix)

Partial Match (0.5): Significant differences but core information present

Ground truth: "Grundriss Erdgeschoss" → Parser: "Grundriss EG" (abbreviation)
Ground truth: "Amalienstraße 45, 80686 München" → Parser: "München" (partial address)

Low Match (0.3): Substantial discrepancy, minimal overlap

Ground truth: "Johann Schmidt Architekten" → Parser: "J. Schmidt" (major abbreviation)

No Match (0.0): Completely incorrect or missing when ground truth exists

Ground truth: "Max Mustermann" → Parser: "John Smith" ✗
Ground truth: "2024-03-15" → Parser: null ✗

Null Handling:

Ground truth is null, Parser is null: Correct (1.0) - correctly identified no data
Ground truth is null, Parser has value: False Positive (0.0) - hallucinated data
Ground truth has value, Parser is null: False Negative (0.0) - missed data

Scoring Dimensions
1. Completeness Score (0-10)
Measures how many fields the parser successfully extracted.
Formula:
Completeness = (Correctly Extracted Fields / Total Non-Null Ground Truth Fields) × 10
Where "Correctly Extracted" means match quality ≥ 0.3 (at least Low Match).
Example:

Ground truth has 5 non-null fields
Parser successfully extracts 4 fields (≥ 0.3 match)
Completeness = (4/5) × 10 = 8.0

2. Accuracy Score (0-10)
Measures the quality of extracted values across all fields.
Formula:
Accuracy = (Sum of all field match scores / Number of fields evaluated) × 10
Evaluate all 7 fields (client, creation_date, drawing_name, project_name, location, scale, architect).
Example:

client: 1.0 (exact)
creation_date: 0.8 (high)
drawing_name: 0.5 (partial)
project_name: 1.0 (exact)
location: 0.0 (no match)
scale: 1.0 (exact)
architect: 0.8 (high)
Accuracy = (5.1 / 7) × 10 = 7.29 → 7.3

3. Overall Score (0-10)
Formula:
Overall Score = (Completeness × 0.4) + (Accuracy × 0.6)
Accuracy is weighted higher because correct extraction is more valuable than just finding something.
Confidence Score Assessment
Evaluate whether the parser's self-reported confidence aligns with actual performance:

Well-Calibrated: Confidence ≈ Actual accuracy (within ±0.2)
Overconfident: Confidence > Actual accuracy (by >0.2)
Underconfident: Confidence < Actual accuracy (by >0.2)

Output Requirements
Return ONLY a valid JSON object with the following structure:
{{
    "field_analysis": {{
        "client": {{"match_score": "value", "note": "brief explanation"}},
        "creation_date": {{"match_score": "value", "note": "brief explanation"}},
        "drawing_name": {{"match_score": "value", "note": "brief explanation"}},
        "project_name": {{"match_score": "value", "note": "brief explanation"}},
        "location": {{"match_score": "value", "note": "brief explanation"}},
        "scale": {{"match_score": "value", "note": "brief explanation"}},
        "architect": {{"match_score": "value", "note": "brief explanation"}}
    }},
    "completeness": "value",
    "accuracy": "value",
    "overall_score": "value",
    "confidence_calibration": "well-calibrated|overconfident|underconfident",
}}
Field Notes Guidelines

Keep notes concise (5-10 words)
State the specific issue: "Date format differs", "Missing street number", "Hallucinated value"
For perfect matches: "Exact match"


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
    message = create_prompt_titleblock(ground_truth,parser_result)
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