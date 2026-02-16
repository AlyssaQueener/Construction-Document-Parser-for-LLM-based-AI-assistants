import src.boq2data.camelot_setup.Camelot_Functions as cam 
import json
import camelot
import src.boq2data.camelot_setup.prompts as prompts 
from mistralai import Mistral


## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)
def call_mistral_boq(path):
    """
    Extract Bill of Quantities (BOQ) data from PDF using hybrid Camelot + Mistral AI approach.
    
    This function implements a two-stage extraction pipeline:
    1. Stage 1 (Deterministic): Camelot extracts raw table data from PDF
    2. Stage 2 (AI): Mistral AI structures, validates, and cleans the extracted data
    
    The hybrid approach leverages:
    - Camelot's reliable table boundary detection and cell extraction
    - Mistral AI's contextual understanding to handle merged cells, inconsistent
      formatting, and semantic grouping of BOQ sections
    
    Args:
        path (str): Path to PDF file containing Bill of Quantities tables
    
    Returns:
        str: JSON string containing structured BOQ data in format:
             {
                 "Sections": [
                     {
                         "section_name": "Foundation Work",
                         "items": [
                             {
                                 "position": "1.1",
                                 "description": "Excavation",
                                 "quantity": 100,
                                 "unit": "m³",
                                 "unit_price": 45.50,
                                 "total": 4550.00
                             }
                         ]
                     }
                 ],
                 "confidence": 0.85
             }
    
    Raises:
        FileNotFoundError: If PDF path is invalid or file doesn't exist
        PDFReadError: If PDF is corrupted, encrypted, or unreadable
    
    Note:
        - Returns raw JSON string (not parsed dict) - parsing happens in extract_boq_mistral()
        - Stream flavor works best for tables without visible gridlines
        - For tables with clear borders, consider changing to flavor="lattice"
    """
    # ============================================================================
    # STAGE 1: TABLE EXTRACTION WITH CAMELOT (DETERMINISTIC)
    # ============================================================================
    
    # Configuration for Camelot PDF table extraction
    page_num = "all"  # Process all pages in the PDF
                      # Alternative: "1,3,4" for specific pages or "1-5" for ranges
    
    flav = "stream"   # Stream algorithm: detects tables by analyzing text positioning
                      # Best for: Tables without borders, modern PDF layouts
                      # Alternative: "lattice" - detects tables by finding line segments
                      # Best for: Tables with visible gridlines, scanned documents
    
    # Extract all tables from PDF using Camelot
    # Returns: TableList object containing detected tables with their data
    tables = camelot.read_pdf(path, flavor=flav, pages=page_num)
    
    # ============================================================================
    # STAGE 2: TABLE PROCESSING AND MERGING
    # ============================================================================
    
    # Process and merge extracted tables into unified JSON structure
    # cam_stream_merge performs:
    # - Merging tables split across multiple pages
    # - Removing header/footer repetitions
    # - Cleaning whitespace and normalizing formatting
    # - Handling merged cells and multi-line content
    # - Converting to JSON-compatible dictionary structure
    tables_boq_processed = cam.cam_stream_merge(tables)
    
    # Convert processed tables to formatted JSON string for LLM consumption
    # indent=2: Makes JSON human-readable with 2-space indentation
    #           (helps LLM understand structure better)
    # ensure_ascii=False: Preserves non-ASCII characters (€, ü, ñ, 中文, etc.)
    #                     Important for international BOQs with special characters
    processed_str = json.dumps(tables_boq_processed, indent=2, ensure_ascii=False)
    
    # ============================================================================
    # STAGE 3: AI STRUCTURING WITH MISTRAL
    # ============================================================================
    
    # Create specialized prompt for BOQ data structuring
    # prompts.create_preproccesed_prompt adds:
    # - Instructions for identifying BOQ sections (structural work, MEP, finishes)
    # - Rules for parsing position numbers (1.1, 1.2.3, etc.)
    # - Guidance for extracting quantities, units, and prices
    # - Schema definition for expected output format
    user_message = prompts.create_preproccesed_prompt(processed_str)
    
    # Construct message array for Mistral chat completion API
    messages = [
        {
            "role": "system",
            # System message enforces strict JSON schema compliance
            # Critical because:
            # 1. Prevents LLM from returning bare arrays (common mistake)
            # 2. Ensures confidence score is always present for quality control
            # 3. Makes downstream parsing predictable and error-free
            "content": "You are a JSON extraction assistant. You MUST return a JSON object with exactly two keys: 'Sections' (array) and 'confidence' (number). Never return a bare array."
        },
        {
            "role": "user",
            "content": user_message,  # Contains preprocessed table data + instructions
        }
    ]
    
    # Call Mistral API for intelligent BOQ structuring
    chat_response = client.chat.complete(
        model=model,  # Model defined globally (e.g., "mistral-small-2503")
        messages=messages,
        response_format={
            "type": "json_object",  # Forces valid JSON output (no markdown, no plaintext)
                                   # Prevents common LLM failure modes:
                                   # - Wrapping JSON in markdown code blocks
                                   # - Adding explanatory text before/after JSON
                                   # - Returning malformed JSON
        }
    )
    
    # Extract the actual response content from API response object
    response = chat_response.choices[0].message.content
    
    # ============================================================================
    # STAGE 4: RESPONSE CLEANING (DEFENSIVE PROGRAMMING)
    # ============================================================================
    
    # Even with response_format="json_object", some edge cases can occur:
    # - Mistral API versions may inconsistently apply format enforcement
    # - Network issues could truncate responses
    # - Custom model fine-tunes might bypass format rules
    # Therefore: defensively clean the response
    
    # Remove leading/trailing whitespace
    response = response.strip()
    
    # Remove markdown JSON code block wrapper if present
    # Example: "```json\n{...}\n```" → "{...}"
    if response.startswith('```json'):
        response = response[7:]  # Remove '```json' (7 characters)
    
    # Remove generic markdown code block wrapper
    # Example: "```\n{...}\n```" → "{...}"
    if response.startswith('```'):
        response = response[3:]  # Remove '```' (3 characters)
    
    # Remove closing code block marker
    if response.endswith('```'):
        response = response[:-3]  # Remove trailing '```'
    
    # Final cleanup of any remaining whitespace
    response = response.strip()
    
    # ============================================================================
    # DEBUG UTILITIES (COMMENTED OUT)
    # ============================================================================
    
    # Uncomment these lines when troubleshooting extraction issues:
    # - LLM returning unexpected format
    # - JSON parsing errors in extract_boq_mistral()
    # - Missing or malformed data in output
    # 
    # print("=" * 80)
    # print("RAW LLM RESPONSE:")
    # print(response[:1000])  # First 1000 chars (avoid overwhelming console)
    # print("=" * 80)
    
    return response


def extract_boq_mistral(path):
    """
    High-level BOQ extraction with validation, error handling, and confidence scoring.
    
    This function wraps call_mistral_boq() with additional logic to:
    - Parse and validate JSON response structure
    - Handle edge cases (bare arrays, missing fields)
    - Calculate extraction success based on confidence threshold
    - Provide consistent return signature for pipeline integration
    
    Args:
        path (str): Path to PDF file containing Bill of Quantities
    
    Returns:
        tuple: (output, method, is_success, confidence)
            - output (dict): Structured BOQ data or error information
                Success format:
                {
                    "Sections": [
                        {
                            "section_name": "Earthwork",
                            "items": [...]
                        }
                    ],
                    "confidence": 0.87
                }
                Error format:
                {
                    "error": "Response is not valid JSON",
                    "raw_response": "malformed string..."
                }
            
            - method (str): Always "hybrid" (indicates Camelot + Mistral pipeline)
            
            - is_success (bool): True if:
                * JSON parsing succeeded AND
                * Confidence score > 0.5
                False if JSON invalid or confidence too low
            
            - confidence (float): AI confidence score (0.0 to 1.0)
                * >0.8: High confidence - data likely very accurate
                * 0.5-0.8: Medium confidence - verify important values
                * <0.5: Low confidence - manual review recommended
                * 0: Parsing failed
    
    Example Usage:
        >>> output, method, success, conf = extract_boq_mistral('project_boq.pdf')
        >>> 
        >>> if success:
        >>>     print(f"Extraction confidence: {conf:.1%}")
        >>>     for section in output['Sections']:
        >>>         print(f"\nSection: {section['section_name']}")
        >>>         print(f"Items: {len(section['items'])}")
        >>>         total_cost = sum(item['total'] for item in section['items'])
        >>>         print(f"Section total: €{total_cost:,.2f}")
        >>> else:
        >>>     print(f"Extraction failed!")
        >>>     if 'error' in output:
        >>>         print(f"Error: {output['error']}")
    
    Note:
        - Confidence threshold of 0.5 is conservative; adjust based on use case
        - For critical financial documents, consider threshold of 0.7 or higher
        - Always validate extracted costs against original PDF manually
    """
    # Initialize return values with safe defaults
    is_success = False
    method = "hybrid"  # Method identifier for tracking/logging
                       # "hybrid" = Camelot (deterministic) + Mistral (AI)
    
    # Call underlying extraction function
    # Returns raw JSON string that needs parsing and validation
    response = call_mistral_boq(path)
    
    # Note: This legacy code is kept for reference but not used
    # Modern approach uses response_format enforcement instead
    # cleaned_response = response.strip().removeprefix('```json\n').removesuffix('\n```')
    
    try:
        # ========================================================================
        # PARSE AND VALIDATE JSON RESPONSE
        # ========================================================================
        
        # Attempt to parse response as valid JSON
        import json
        output = json.loads(response)
        
        # ========================================================================
        # HANDLE EDGE CASE: LLM RETURNED LIST INSTEAD OF DICT
        # ========================================================================
        
        # Edge case: Despite system message, LLM sometimes returns:
        # [{"section": "...", "items": [...]}]  ← bare array
        # Instead of expected:
        # {"Sections": [...], "confidence": 0.8}  ← proper object
        #
        # This happens when:
        # - LLM ignores system instructions
        # - Prompt is ambiguous
        # - Model fine-tuning overrides instructions
        if isinstance(output, list):
            print("Warning: LLM returned a list instead of expected object structure")
            
            # Defensive fix: Wrap list in expected structure
            # This maintains consistency for downstream code
            output = {
                "Sections": output,
                "confidence": 0.5  # Default to medium confidence
                                  # Lower than normal because structure wasn't followed
                                  # (indicates LLM may have misunderstood task)
            }
        
        # ========================================================================
        # EXTRACT CONFIDENCE AND VALIDATE QUALITY
        # ========================================================================
        
        # Safely extract confidence score
        # .get() with default 0 prevents KeyError if confidence is missing
        # Missing confidence could indicate:
        # - LLM didn't follow instructions
        # - Response was truncated
        # - Schema mismatch
        confidence = output.get("confidence", 0)
        
        # Validate extraction quality using confidence threshold
        # Threshold of 0.5 (50%) is conservative but reasonable:
        # - Higher threshold (0.7): More false negatives, fewer errors
        # - Lower threshold (0.3): Fewer false negatives, more errors
        # Adjust based on your accuracy vs. coverage requirements
        if confidence > 0.5:
            is_success = True
        
        return output, method, is_success, confidence
        
    except json.JSONDecodeError as e:
        # ========================================================================
        # HANDLE JSON PARSING FAILURE
        # ========================================================================
        
        # JSON parsing failed - possible causes:
        # 1. LLM generated invalid JSON (mismatched brackets, trailing commas)
        # 2. Response truncated due to token limit
        # 3. Special characters not properly escaped
        # 4. LLM hallucinated non-JSON content despite format enforcement
        # 5. Network error corrupted response
        
        # Return detailed error information for debugging
        return {
            "error": "Response is not valid JSON",
            "raw_response": response  # Include raw response for manual inspection
                                     # Useful for:
                                     # - Identifying what went wrong
                                     # - Adjusting prompts
                                     # - Reporting API issues
        }, method, False, 0  # is_success=False, confidence=0


