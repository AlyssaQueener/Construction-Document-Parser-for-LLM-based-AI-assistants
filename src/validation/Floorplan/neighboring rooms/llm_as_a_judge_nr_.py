import json
from typing import Dict, Any
from mistralai import Mistral

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)

def create_prompt_neighboring_rooms(ground_truth, parser_result):
    """
    Evaluation prompt for neighboring rooms extraction evaluation, LLM as a judge
    """
    prompt = f"""
Floorplan Neighboring Rooms Parser Evaluation
You are an expert evaluator assessing the performance of an automated parser that extracts room adjacency relationships from architectural floorplans using Voronoi diagrams. Your task is to compare the parser's output against ground truth data and provide a quantitative evaluation.

Input Data
You will receive two JSON objects:

Ground Truth: The correct room adjacency information
Parser Output: The adjacency relationships extracted by the automated parser

Both are dictionaries where:
- Keys are room names (e.g., "Kitchen", "Bedroom_2")
- Values are lists of neighboring room names

Example:
{{
  "Kitchen": ["Living", "Dining", "Entrance"],
  "Living": ["Kitchen", "Bedroom", "Entrance"]
}}

Evaluation Methodology

Room-Level Matching Rules

For each room in the ground truth, evaluate:

1. Room Name Match
   - Exact Match (1.0): Room name exists in parser output exactly
     Ground truth: "Kitchen" → Parser: "Kitchen" ✓
   
   - Close Match (0.8): Minor differences (case, spacing, numbering)
     Ground truth: "Bedroom 1" → Parser: "Bedroom_1"
     Ground truth: "WC" → Parser: "wc"
   
   - Semantic Match (0.6): Different name but clearly same room
     Ground truth: "Living Room" → Parser: "Living"
     Ground truth: "Bathroom" → Parser: "WC"
   
   - No Match (0.0): Room not found in parser output
     Ground truth: "Kitchen" → Parser: (missing) ✗

2. Neighbor List Accuracy (for matched rooms)
   
   Calculate precision and recall for each room's neighbor list:
   
   - True Positives (TP): Neighbors correctly identified
   - False Positives (FP): Neighbors incorrectly added (hallucinated)
   - False Negatives (FN): Neighbors missed
   
   Precision = TP / (TP + FP)
   Recall = TP / (TP + FN)
   F1 Score = 2 × (Precision × Recall) / (Precision + Recall)
   
   When comparing neighbor names, use fuzzy matching (similar to room name matching above).
   
   Example:
   Ground truth "Kitchen": ["Living", "Dining", "Entrance"]
   Parser "Kitchen": ["Living", "Dining", "Hallway"]
   
   TP = 2 (Living, Dining)
   FP = 1 (Hallway - not in ground truth)
   FN = 1 (Entrance - missed)
   
   Precision = 2/(2+1) = 0.667
   Recall = 2/(2+1) = 0.667
   F1 = 0.667

Scoring Dimensions

1. Room Detection Score (0-10)
Measures how many rooms the parser successfully identified.

Formula:
Room Detection = (Successfully Detected Rooms / Total Ground Truth Rooms) × 10

Where "Successfully Detected" means room name match quality ≥ 0.6.

Example:
- Ground truth has 8 rooms
- Parser correctly identifies 7 rooms (≥ 0.6 match)
- Room Detection = (7/8) × 10 = 8.75 → 8.8

2. Adjacency Precision (0-10)
Measures how many of the parser's identified adjacencies are correct.

Formula:
Precision = (Average Precision across all rooms) × 10

Only include rooms that exist in both ground truth and parser output.

Example:
- Room1 precision: 1.0
- Room2 precision: 0.75
- Room3 precision: 0.67
- Average = 0.807
- Precision Score = 8.1

3. Adjacency Recall (0-10)
Measures how many true adjacencies the parser found.

Formula:
Recall = (Average Recall across all rooms) × 10

Only include rooms that exist in both ground truth and parser output.

4. Adjacency F1 Score (0-10)
Harmonic mean of precision and recall.

Formula:
F1 = (Average F1 across all rooms) × 10

5. Overall Score (0-10)
Formula:
Overall Score = (Room Detection × 0.3) + (F1 Score × 0.7)

F1 is weighted higher because correct adjacency relationships are more valuable than just detecting room names.

Special Cases

- Missing Rooms: If a room exists in ground truth but not in parser output, it gets:
  - Room name match: 0.0
  - Cannot evaluate neighbors (contributes to Room Detection penalty)

- Extra Rooms: If parser output contains rooms not in ground truth:
  - Note as "hallucinated rooms" in analysis
  - Do not penalize directly, but affects precision scores

- Bidirectional Consistency: Check if adjacencies are symmetric:
  If "Kitchen" lists "Living" as neighbor, "Living" should list "Kitchen"
  Report any asymmetries in the detailed analysis

- Self-References: Flag if any room lists itself as a neighbor (error)

Output Requirements

Return ONLY a valid JSON object with the following structure:

{{
    "room_analysis": {{
        "Room1": {{
            "name_match_score": 1.0,
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "true_positives": ["neighbor1", "neighbor2"],
            "false_positives": ["neighbor3"],
            "false_negatives": ["neighbor4"],
            "note": "brief explanation"
        }}
    }},
    "summary": {{
        "total_rooms_ground_truth": 10,
        "total_rooms_parser": 10,
        "rooms_correctly_detected": 10,
        "hallucinated_rooms": [],
        "missing_rooms": [],
        "asymmetric_adjacencies": []
    }},
    "room_detection_score": 10.0,
    "adjacency_precision": 10.0,
    "adjacency_recall": 10.0,
    "adjacency_f1_score": 10.0,
    "overall_score": 10.0,
    "key_issues": []
}}

Field Notes Guidelines:
- Keep notes concise (10-15 words)
- State specific issues: "Missed bathroom adjacency", "Hallucinated connection to hallway"
- For perfect matches: "All neighbors correctly identified"
- Highlight critical errors: "Self-reference detected", "Asymmetric adjacency"

Ground Truth Data:
{json.dumps(ground_truth, indent=2)}

Parser Output Data:
{json.dumps(parser_result, indent=2)}

Begin your evaluation now. Return only the JSON output with no additional text.
"""
    return prompt


def read_json(path_to_json_file):
    """Read JSON file and return parsed data."""
    with open(path_to_json_file, 'r', encoding='utf-8') as json_data:
        df = json.load(json_data)
    return df


def call_mistral_evaluation(ground_truth: Dict[str, Any], parser_result: Dict[str, Any]) -> str | None:
    """Call Mistral API with evaluation prompt."""
    message = create_prompt_neighboring_rooms(ground_truth, parser_result)
    
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
            
            # Debug: Print raw response
            print("\n=== RAW RESPONSE ===")
            print(f"Content type: {type(content)}")
            
            # content is typically a string when using json_object response format
            if isinstance(content, str):
                response_text = content
            else:
                print(f"Unexpected content type: {type(content)}")
                print(f"Content: {content}")
                return None
            
            print(response_text[:500])  # First 500 chars
            print("...\n")
            
            # Validate it's proper JSON
            try:
                parsed = json.loads(response_text)
                return response_text
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Response text: {response_text}")
                return None
        else:
            print("No choices in response")
            return None
        
    except Exception as e:
        print(f"Error during API call: {e}")
        import traceback
        traceback.print_exc()
        return None


def llm_as_a_judge_nr(path_to_ground_truth: str, path_to_parser_result: str, output_path: str = None) -> str | None:
    """Main evaluation function."""
    print(f"Reading ground truth from: {path_to_ground_truth}")
    ground_truth = read_json(path_to_ground_truth)
    
    print(f"Reading parser result from: {path_to_parser_result}")
    parser_result = read_json(path_to_parser_result)
    
    # Debug: Print data structure info
    print(f"\nGround truth structure:")
    print(f"  Type: {type(ground_truth)}")
    if isinstance(ground_truth, dict):
        print(f"  Number of rooms: {len(ground_truth)}")
        print(f"  Sample rooms: {list(ground_truth.keys())[:3]}")
    
    print(f"\nParser result structure:")
    print(f"  Type: {type(parser_result)}")
    if isinstance(parser_result, dict):
        print(f"  Number of rooms: {len(parser_result)}")
        print(f"  Sample rooms: {list(parser_result.keys())[:3]}")
    
    print("\nCalling Mistral API...")
    evaluation_result = call_mistral_evaluation(ground_truth, parser_result)
    
    # Save result if output path provided
    if evaluation_result and output_path:
        try:
            result_dict = json.loads(evaluation_result)
            with open(output_path, "w", encoding='utf-8') as file:
                json.dump(result_dict, file, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    return evaluation_result


if __name__ == "__main__":
    groundtruth = "src/validation/Floorplan/neighboring rooms/testdata_ai/Cluttered_03_ai copy.json"
    parserresult = "src/validation/Floorplan/neighboring rooms/testdata_ai/Cluttered_03_ai.json"
    output_path = "src/validation/Floorplan/neighboring rooms/LLM as a judge output ai/Cluttered 02_neighbors_ai_llm.json"
    #output_path = groundtruth.replace('val.json', 'llm_as_judge.json')
    evaluation_result = llm_as_a_judge_nr(groundtruth, parserresult, output_path)
    
    if evaluation_result:
        print("\n=== FINAL RESULT ===")
        # Pretty print the JSON
        result_dict = json.loads(evaluation_result)
        print(json.dumps(result_dict, indent=2))
    else:
        print("\nEvaluation failed!")