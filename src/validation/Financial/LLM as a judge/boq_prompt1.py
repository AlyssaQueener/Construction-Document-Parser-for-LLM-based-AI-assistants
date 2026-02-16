import json
from mistralai import Mistral
from mistralai.client import MistralClient


## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
import json
from mistralai import Mistral
from typing import Any, Dict

model = "mistral-small-2503"
client = Mistral(api_key=api_key)


def create_prompt_boq(ground_truth: Dict[str, Any], parser_result: Dict[str, Any]) -> str:
    """
    Evaluation prompt for Bill of Quantity extraction evaluation, LLM as a judge.
    """
    # Convert to JSON strings with proper formatting
    gt_json = json.dumps(ground_truth, indent=2)
    pr_json = json.dumps(parser_result, indent=2)
    
    prompt = f"""You are evaluating a Bill of Quantity (BoQ) parser by comparing its output against ground truth data.

GROUND TRUTH DATA:
{gt_json}

PARSER OUTPUT DATA:
{pr_json}

EVALUATION INSTRUCTIONS:

1. Match items between ground truth and parser output using Internal Number (preferred) or Item Number + Section Title
2. For each matched item, evaluate these fields: item_number, item_description, unit, quantity, rate, amount, currency
3. Score each field (0.0 to 1.0):
   - 1.0: Exact match
   - 0.8: Minor formatting difference
   - 0.5: Core info present, some differences
   - 0.3: Minimal overlap
   - 0.0: Incorrect/missing
4. Calculate:
   - Completeness: (items with ≥5 fields scoring ≥0.3) / total ground truth items × 10
   - Accuracy: average of all field scores × 10
   - Overall: (Completeness × 0.4) + (Accuracy × 0.6)

Return ONLY valid JSON in this exact format:
{{
  "section_analysis": [
    {{
      "section_title": "string",
      "item_analysis": [
        {{
          "internal_number": "string or number",
          "match_scores": {{
            "item_number": 0.0,
            "item_description": 0.0,
            "unit": 0.0,
            "quantity": 0.0,
            "rate": 0.0,
            "amount": 0.0,
            "currency": 0.0
          }},
          "notes": {{
            "item_number": "brief note",
            "item_description": "brief note",
            "unit": "brief note",
            "quantity": "brief note",
            "rate": "brief note",
            "amount": "brief note",
            "currency": "brief note"
          }}
        }}
      ]
    }}
  ],
  "completeness": 0.0,
  "accuracy": 0.0,
  "overall_score": 0.0,
  "confidence_calibration": "well-calibrated"
}}

Begin evaluation now."""
    return prompt


def read_json(path_to_json_file: str) -> Dict[str, Any]:
    """Read JSON file and return parsed data."""
    with open(path_to_json_file, 'r', encoding='utf-8') as json_data:
        return json.load(json_data)


def call_mistral_evaluation(ground_truth: Dict[str, Any], parser_result: Dict[str, Any]) -> str | None:
    """Call Mistral API with evaluation prompt."""
    message = create_prompt_boq(ground_truth, parser_result)
    
    # Debug: Print prompt length
    print(f"Prompt length: {len(message)} characters")
    print(f"Estimated tokens: ~{len(message) // 4}")
    
    try:
        chat_response = client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
            response_format={
                "type": "json_object",
            }
        )
        
        # Handle the response properly
        if chat_response.choices and len(chat_response.choices) > 0:
            content = chat_response.choices[0].message.content
            
            # content could be a string or list of content chunks
            if isinstance(content, str):
                response_text = content
            elif isinstance(content, list):
                # Combine text chunks if it's a list
                text_parts = []
                for chunk in content:
                    if hasattr(chunk, 'text') and chunk.text:
                        text_parts.append(str(chunk.text))
                    elif isinstance(chunk, str):
                        text_parts.append(chunk)
                response_text = "".join(text_parts)
            else:
                print(f"Unexpected content type: {type(content)}")
                return None
            
            # Debug: Print raw response
            print("\n=== RAW RESPONSE ===")
            print(response_text[:500])  # First 500 chars
            print("...\n")
            
            # Validate it's proper JSON
            parsed = json.loads(response_text)
            return response_text
        else:
            print("No choices in response")
            return None
        
    except Exception as e:
        print(f"Error during API call: {e}")
        import traceback
        traceback.print_exc()
        return None


def llm_as_a_judge_boq(path_to_ground_truth: str, path_to_parser_result: str) -> str | None:
    """Main evaluation function."""
    print(f"Reading ground truth from: {path_to_ground_truth}")
    ground_truth = read_json(path_to_ground_truth)
    
    print(f"Reading parser result from: {path_to_parser_result}")
    parser_result = read_json(path_to_parser_result)
    
    # Debug: Print data structure info
    print(f"\nGround truth structure:")
    print(f"  Type: {type(ground_truth)}")
    if isinstance(ground_truth, dict):
        print(f"  Keys: {list(ground_truth.keys())}")
    elif isinstance(ground_truth, list):
        print(f"  Length: {len(ground_truth)}")
        if ground_truth:
            print(f"  First item keys: {list(ground_truth[0].keys()) if isinstance(ground_truth[0], dict) else 'N/A'}")
    
    print(f"\nParser result structure:")
    print(f"  Type: {type(parser_result)}")
    if isinstance(parser_result, dict):
        print(f"  Keys: {list(parser_result.keys())}")
    elif isinstance(parser_result, list):
        print(f"  Length: {len(parser_result)}")
        if parser_result:
            print(f"  First item keys: {list(parser_result[0].keys()) if isinstance(parser_result[0], dict) else 'N/A'}")
    
    print("\nCalling Mistral API...")
    evaluation_result = call_mistral_evaluation(ground_truth, parser_result)
    
    return evaluation_result


if __name__ == "__main__":
    groundtruth = "Construction-Document-Parser-for-LLM-based-AI-assistants/src/validation/Financial/LLM as a judge/testdata/BOQ4_validation_boq_data.json"
    parserresult = "Construction-Document-Parser-for-LLM-based-AI-assistants/src/validation/Financial/LLM as a judge/testdata/BOQ4_extracted_boq_data.json"
    
    evaluation_result = llm_as_a_judge_boq(groundtruth, parserresult)
    
    if evaluation_result:
        print("\n=== FINAL RESULT ===")
        # Pretty print the JSON
        result_dict = json.loads(evaluation_result)
        print(json.dumps(result_dict, indent=2))
        path = "Construction-Document-Parser-for-LLM-based-AI-assistants/src/validation/Financial/LLM as a judge/BOQ4_output.json"
        with open(path, "w") as file:
            json.dump(result_dict, file, indent=2)
    else:
        print("\nEvaluation failed!")