import json
from mistralai import Mistral
from mistralai.client import MistralClient


## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)


def create_prompt_boq(ground_truth, parser_result):
    """
    Evaluation prompt for Bill of Quantity extraction evaluation, LLM as a judge.
    """
    prompt = f"""
Bill of Quantity Parser Evaluation
You are an expert evaluator assessing the performance of an automated parser that extracts Bill of Quantity (BoQ) information from construction documents. Your task is to compare the parser's output against ground truth BoQ data and provide a quantitative evaluation.

Input Data
You will receive two JSON objects:

Ground Truth: The correct Bill of Quantity information
Parser Output: The BoQ information extracted by the automated parser

Each object consists of one or more sections. Every section contains:
  - Section Title
  - Items (list):
    - Internal Number
    - Item Number
    - Item Description
    - Unit
    - Quantity
    - Rate
    - Amount
    - Currency (can be null)

Evaluation Methodology

Field-Level Matching Rules
For each matching pair of items (based on Internal Number or Item Number and Section Title), evaluate each field:
- Exact Match (1.0): Values are identical (case-insensitive, whitespace-normalized)
- High Match (0.8): Minor formatting (e.g., "m²" vs "sqm", "L.S." vs "Lump Sum")
- Partial Match (0.5): Core information present, but major abbreviation, minor omission, or order swapped ("Terracing site" ↔ "Terracing for site levelling")
- Low Match (0.3): Minimal overlap, substantial discrepancy
- No Match (0.0): Incorrect, missing, or hallucinated value when ground truth exists

Null Handling:
- Ground truth null, parser null: Correct (1.0)
- Ground truth null, parser value: False Positive (0.0)
- Ground truth value, parser null: Missed data (0.0)

Section and Item Matching:
- Try to pair items using Internal Number first (if available), otherwise Item Number and Section Title. If item missing, mark as No Match for all fields.

Scoring Dimensions

1. Completeness Score (0-10)
Percentage of items for which at least 5 of 8 fields are correctly matched (≥0.3), considering only items present in ground truth.

Formula:
Completeness = (Correctly Extracted Items / Total Non-Null Ground Truth Items) × 10

2. Accuracy Score (0-10)
Field-level average match quality across all matched items and fields.

Formula:
Accuracy = (Sum of all field match scores / Number of fields evaluated) × 10

3. Overall Score (0-10)
Weighted average: Completeness × 0.4 + Accuracy × 0.6

Confidence Score Assessment
If parser reports any confidence value per item or globally, assess calibration:
- Well-Calibrated: Confidence ≈ Actual accuracy (±0.2)
- Overconfident/Underconfident: Deviation >0.2

Output Requirements
Return ONLY a valid JSON object:
{{
    "section_analysis": [
        {{
            "section_title": "...",
            "item_analysis": [
                {{
                    "internal_number": ...,
                    "match_scores": {{
                        "item_number": "value",
                        "item_description": "value",
                        "unit": "value",
                        "quantity": "value",
                        "rate": "value",
                        "amount": "value",
                        "currency": "value"
                    }},
                    "notes": {{
                        "item_number": "...",
                        "item_description": "...",
                        "unit": "...",
                        "quantity": "...",
                        "rate": "...",
                        "amount": "...",
                        "currency": "..."
                    }}
                }},
                ...
            ]
        }},
        ...
    ],
    "completeness": "value",
    "accuracy": "value",
    "overall_score": "value",
    "confidence_calibration": "well-calibrated|overconfident|underconfident",
}}
Field Notes Guidelines
- Notes per field: concise (5-10 words), state specific issue ("Unit abbreviation differs", "Missing from parser", "Exact match", "Partial quantity", "Amount mismatch")
- For perfect matches: "Exact match"

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
    message = create_prompt_boq(ground_truth,parser_result)
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

def llm_as_a_judge_boq(path_to_ground_truth, parsing_result):
    ground_truth = read_json(path_to_ground_truth)
    evaluation_result = call_mistral_evaluation(ground_truth,parsing_result)
    return evaluation_result

if __name__ == "__main__":
    groundtruth = "Construction-Document-Parser-for-LLM-based-AI-assistants/output/Financial/BOQ1_validation_boq_data.json"
    parserresult = "Construction-Document-Parser-for-LLM-based-AI-assistants/output/Financial/BOQ1_extracted_boq_data.json"
    evaluation_result = llm_as_a_judge_boq(groundtruth, parserresult)
    print(evaluation_result)