import json
from mistralai import Mistral

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)
def create_prompt_titleblock(groundt_truth, parser_result):
    """
    Evaluation prompt for title block extraction evaluation, llm as a judge
    """
    prompt = f"""
 Task: Evaluate Floorplan Title Block Parser Output

You are an expert evaluator assessing the quality of a parser that extracts title block information from architectural floorplans. Your task is to compare the parser's output against ground truth data and provide a detailed evaluation.

## Input Format
You will be provided with:
1. **Ground Truth**: The correct title block information extracted from the floorplan
2. **Parser Output**: The information extracted by the automated parser

## Evaluation Criteria

Evaluate the parser output across the following dimensions:

### 1. Completeness (0-10)
- Are all fields present in the ground truth also extracted by the parser?
- Missing fields should reduce the score proportionally

### 2. Accuracy (0-10)
- How accurate is each extracted field compared to the ground truth?
- Consider:
  - Exact matches (full credit)
  - Minor discrepancies (e.g., formatting differences, extra/missing spaces)
  - Partial matches (e.g., abbreviated vs. full terms)
  - Complete mismatches (no credit)


## Evaluation Steps

1. **Inventory Check**: List all fields present in ground truth and parser output
3. **Score Assignment**: Assign scores for Completeness, Accuracy
4. **Calculate Overall Score**: Average of the two dimension scores
5. **Provide Summary**: 
   - Overall score (0-10)
   - Key strengths of the parser
   - Main weaknesses or failure modes
   - Specific recommendations for improvement

## Output Format

**Scores:**
- Completeness: X/10
- Accuracy: X/10
- **Overall Score: X/10**

**Summary:**
[Provide 2-3 sentences on overall performance]

**Strengths:**
[List key strengths]

**Weaknesses:**
[List main issues]

**Recommendations:**
[Suggest specific improvements]

please return the evaluation result only in valid json:

{{
    "completeness": "value",
    "accuracy": "value",
    "overall score": "value", 
    "strengths": "value",
    "weakness": "value",
    "recommendations": "value",
}}

GROUND TRUTH:
{groundt_truth}

PARSER RESULT:
{parser_result}
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

def llm_as_a_judge_titleblock(path_to_ground_truth, parsing_result):
    ground_truth = read_json(path_to_ground_truth)
    evaluation_result = call_mistral_evaluation(ground_truth,parsing_result)
    return evaluation_result