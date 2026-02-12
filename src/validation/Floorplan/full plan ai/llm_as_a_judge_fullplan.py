import json
from mistralai import Mistral

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)
def create_prompt_full_plan_ai(ground_truth, parser_result):
    """
    Combined evaluation prompt for full plan AI extraction (title block + neighboring rooms)
    """
    prompt = f"""
Floorplan Full Plan AI Parser Evaluation

You are an expert evaluator assessing the performance of an automated parser that extracts both title block information AND room adjacency relationships from architectural floorplans. Your task is to compare the parser's output against ground truth data and provide a quantitative evaluation.

Input Data Structure

You will receive two JSON objects with nested structure:

1. Title Block Section:
   - projectInfo:
     - projectId, projectName, location, author
     - stakeholders: client, architect, engineers (array)
     - timeline: yearOfCompletion, approvalDate
   - planMetadata:
     - planType, planFormat, scale, projectionMethod

2. Room Adjacency Section:
   - neighboring_rooms: Dictionary where keys are room names and values are lists of neighboring room names

Example:
{{
  "projectInfo": {{
    "projectId": "P-2024-001",
    "projectName": "Residential Building",
    ...
  }},
  "planMetadata": {{
    "planType": "Grundriss",
    ...
  }},
  "neighboring_rooms": {{
    "Kitchen": ["Living", "Dining"],
    "Living": ["Kitchen", "Bedroom"]
  }}
}}

═══════════════════════════════════════════════════════════════════════════════
PART 1: TITLE BLOCK EVALUATION
═══════════════════════════════════════════════════════════════════════════════

Field-Level Matching Rules

Exact Match (1.0): Values are identical (case-insensitive, whitespace-normalized)
- Ground truth: "Max Mustermann" → Parser: "Max Mustermann" ✓
- Ground truth: "1:100" → Parser: "1:100" ✓
- Ground truth: ["Engineer A", "Engineer B"] → Parser: ["Engineer A", "Engineer B"] ✓

High Match (0.8): Minor formatting differences, but semantically identical
- Ground truth: "15.03.2024" → Parser: "2024-03-15" (date format conversion)
- Ground truth: "M 1:100" → Parser: "1:100" (notation difference)
- Ground truth: "Schmidt & Partner" → Parser: "Schmidt & Partner GmbH" (added suffix)
- Ground truth: "A1" → Parser: "841×594mm" (equivalent formats)

Partial Match (0.5): Significant differences but core information present
- Ground truth: "Grundriss Erdgeschoss" → Parser: "Grundriss EG" (abbreviation)
- Ground truth: "Amalienstraße 45, 80686 München" → Parser: "München" (partial address)
- Ground truth: ["Engineer A", "Engineer B"] → Parser: ["Engineer A"] (subset of array)
- Ground truth: "2025" → Parser: "2025-12-31" (year vs full date)

Low Match (0.3): Substantial discrepancy, minimal overlap
- Ground truth: "Johann Schmidt Architekten" → Parser: "J. Schmidt" (major abbreviation)
- Ground truth: ["Engineer A", "Engineer B", "Engineer C"] → Parser: ["Engineer A"] (missing majority)

No Match (0.0): Completely incorrect or missing when ground truth exists
- Ground truth: "Max Mustermann" → Parser: "John Smith" ✗
- Ground truth: "2024-03-15" → Parser: null ✗
- Ground truth: ["Engineer A"] → Parser: ["Engineer X"] ✗

None Value Handling:
- Ground truth is None, Parser is None: Correct (1.0) - correctly identified no data
- Ground truth is None, Parser has value: False Positive (0.0) - hallucinated data
- Ground truth has value, Parser is None: False Negative (0.0) - missed data

Array Field Handling (engineers):
- Exact Match (1.0): All items present and correct
- High Match (0.8): 80-99% of items present
- Partial Match (0.5): 50-79% of items present
- Low Match (0.3): 20-49% of items present
- No Match (0.0): <20% overlap or completely wrong

Title Block Scoring

1. Title Block Completeness (0-10)
Formula:
Completeness = (Correctly Extracted Fields / Total Non-Null Ground Truth Fields) × 10

Count all 13 leaf fields:
- projectInfo: projectId, projectName, location, author (4 fields)
- projectInfo.stakeholders: client, architect, engineers (3 fields)
- projectInfo.timeline: yearOfCompletion, approvalDate (2 fields)
- planMetadata: planType, planFormat, scale, projectionMethod (4 fields)

"Correctly Extracted" means match quality ≥ 0.3 (at least Low Match).

2. Title Block Accuracy (0-10)
Formula:
Accuracy = (Sum of all field match scores / 13 fields) × 10

Evaluate all 13 leaf fields regardless of whether they exist in ground truth.

═══════════════════════════════════════════════════════════════════════════════
PART 2: ROOM ADJACENCY EVALUATION
═══════════════════════════════════════════════════════════════════════════════

Room-Level Matching Rules

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

Room Adjacency Scoring

1. Room Detection Score (0-10)
Formula:
Room Detection = (Successfully Detected Rooms / Total Ground Truth Rooms) × 10

Where "Successfully Detected" means room name match quality ≥ 0.6.

2. Adjacency Precision (0-10)
Formula:
Precision = (Average Precision across all matched rooms) × 10

Only include rooms that exist in both ground truth and parser output.

3. Adjacency Recall (0-10)
Formula:
Recall = (Average Recall across all matched rooms) × 10

4. Adjacency F1 Score (0-10)
Formula:
F1 = (Average F1 across all matched rooms) × 10

Special Cases for Room Adjacency

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

═══════════════════════════════════════════════════════════════════════════════
OVERALL COMBINED SCORING
═══════════════════════════════════════════════════════════════════════════════

1. Title Block Score (0-10)
Formula:
Title Block Score = (Title Block Completeness × 0.4) + (Title Block Accuracy × 0.6)

2. Room Adjacency Score (0-10)
Formula:
Room Adjacency Score = (Room Detection × 0.3) + (Adjacency F1 × 0.7)

3. Overall Score (0-10)
Formula:
Overall Score = (Title Block Score × 0.4) + (Room Adjacency Score × 0.6)

Room adjacency is weighted higher as it's typically more complex and valuable for downstream applications.

═══════════════════════════════════════════════════════════════════════════════
OUTPUT REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Return ONLY a valid JSON object with the following structure:

{{
    "title_block_analysis": {{
        "field_analysis": {{
            "projectInfo": {{
                "projectId": {{"match_score": 1.0, "note": "Exact match"}},
                "projectName": {{"match_score": 0.8, "note": "Minor formatting difference"}},
                "location": {{"match_score": 0.5, "note": "Partial address only"}},
                "author": {{"match_score": 1.0, "note": "Exact match"}},
                "stakeholders": {{
                    "client": {{"match_score": 1.0, "note": "Exact match"}},
                    "architect": {{"match_score": 0.8, "note": "Added GmbH suffix"}},
                    "engineers": {{"match_score": 0.5, "note": "Found 1 of 2 engineers"}}
                }},
                "timeline": {{
                    "yearOfCompletion": {{"match_score": 1.0, "note": "Exact match"}},
                    "approvalDate": {{"match_score": 0.0, "note": "Missing"}}
                }}
            }},
            "planMetadata": {{
                "planType": {{"match_score": 1.0, "note": "Exact match"}},
                "planFormat": {{"match_score": 0.8, "note": "Equivalent format"}},
                "scale": {{"match_score": 1.0, "note": "Exact match"}},
                "projectionMethod": {{"match_score": 0.0, "note": "Missing"}}
            }}
        }},
        "completeness": 8.5,
        "accuracy": 7.2,
        "title_block_score": 7.7,
        "confidence_calibration": "well-calibrated"
    }},
    "room_adjacency_analysis": {{
        "room_analysis": {{
            "Kitchen": {{
                "name_match_score": 1.0,
                "precision": 0.8,
                "recall": 0.9,
                "f1": 0.85,
                "true_positives": ["Living", "Dining"],
                "false_positives": ["Hallway"],
                "false_negatives": [],
                "note": "One hallucinated neighbor"
            }},
            "Living": {{
                "name_match_score": 1.0,
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
                "true_positives": ["Kitchen", "Bedroom"],
                "false_positives": [],
                "false_negatives": [],
                "note": "All neighbors correctly identified"
            }}
        }},
        "summary": {{
            "total_rooms_ground_truth": 8,
            "total_rooms_parser": 8,
            "rooms_correctly_detected": 8,
            "hallucinated_rooms": [],
            "missing_rooms": [],
            "asymmetric_adjacencies": []
        }},
        "room_detection_score": 10.0,
        "adjacency_precision": 9.0,
        "adjacency_recall": 9.5,
        "adjacency_f1_score": 9.2,
        "room_adjacency_score": 9.4
    }},
    "overall_score": 8.7,
    "key_issues": [
        "Title block: Missing approval date",
        "Room adjacency: Kitchen has hallucinated Hallway connection"
    ]
}}

Field Notes Guidelines:
- Keep notes concise (5-15 words)
- State specific issues clearly
- For perfect matches: "Exact match" or "All neighbors correctly identified"
- For arrays: Mention counts if partial (e.g., "Found 1 of 2 engineers")
- Highlight critical errors: "Self-reference detected", "Asymmetric adjacency", "Hallucinated value"

Ground Truth Data:
{json.dumps(ground_truth, indent=2)}

Parser Output Data:
{json.dumps(parser_result, indent=2)}

Begin your evaluation now. Return only the JSON output with no additional text.
"""
    return prompt


def read_json(path_to_json_file):
    with open(path_to_json_file) as json_data:
        df = json.load(json_data)
        json_data.close()
        return df

def call_mistral_evaluation(ground_truth, parser_result):
    message = create_prompt_full_plan_ai(ground_truth,parser_result)
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

def llm_as_a_judge_full_plan_ai(path_to_ground_truth: str, path_to_parser_result: str, output_path: str = None) -> str | None:
    """Main evaluation function."""
    print(f"Reading ground truth from: {path_to_ground_truth}")
    ground_truth = read_json(path_to_ground_truth)
    
    print(f"Reading parser result from: {path_to_parser_result}")
    parser_result = read_json(path_to_parser_result)
    
     
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
    groundtruth = "src/validation/Floorplan/full plan ai/Floorplan_Test_02 val..json"
    parserresult = "src/validation/Floorplan/full plan ai/Floorplan_Test_02.json"
    output_path = "src/validation/Floorplan/full plan ai/LLM as a judge ouput//Floorplan_Test_02_eval_output.json"
    
    evaluation_result = llm_as_a_judge_full_plan_ai(groundtruth, parserresult, output_path)
    
    if evaluation_result:
        print("\n=== FINAL RESULT ===")
        # Pretty print the JSON
        result_dict = json.loads(evaluation_result)
        print(json.dumps(result_dict, indent=2))
    else:
        print("\nEvaluation failed!")