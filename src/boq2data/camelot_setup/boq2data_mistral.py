import os
import google.generativeai as genai
import json

api_key = "AIzaSyD22tv_jw44Cnqp3J_9J-_1s85e5epop9s"

def create_preprocessed_prompt(extracted_text):
    """
    Constructs a detailed prompt for Gemini to extract structured,
    section-grouped information from a Bill of Quantities (BoQ).
    
    This function generates a comprehensive prompt that instructs the Gemini API
    to parse BOQ documents (in English or German) and extract structured data
    including section hierarchies, line items, and subtotals in a specific JSON format.
    
    Args:
        extracted_text (str): Raw text extracted from a BOQ PDF (typically from Camelot)
    
    Returns:
        str: Formatted prompt string for the Gemini API containing:
             - Extraction instructions
             - JSON schema definitions
             - Example structures for nested and flat sections
             - Field definitions and validation rules
    
    Note:
        - Supports both English and German BOQ documents
        - Handles nested subsections with arbitrary depth
        - Includes subtotals as the last item in each section when present
        - All monetary values should preserve original precision
    """
    prompt = f"""
You are an expert system for extracting structured data from English or German Bills of Quantities (BoQs).

🔧 Your task:
- Extract item rows and organize them into a JSON array.
- Group each section under a key called "Section Title".
- Sometimes there are subsection titles under the section titles — if present, include them as "Subsection Title" or as nested "Subsections".
- Each section should contain an "Items" list of the line items.
- Include valid **subtotals only if present** as the **last item** in the Items array of each section.

📌 JSON Structure Examples:

If there are nested subsections:
[
  {{
    "Section Title": "2.5 Excavating & filling",
    "Subsections": [
      {{
        "Subsection Title": "2.5.1 Fillings",
        "Subsections": [
          {{
            "Subsection Title": "2.5.1.1 Filling obtained from excavated material",
            "Items": [
              {{
                "Internal Number": "0",
                "Item Number": "2.5.1.1.1",
                "Item Description": "Fill obtained from temporary spoil heaps ...",
                "Unit": "m³",
                "Quantity": "150",
                "Rate": "25.00",
                "Amount": "3750.00",
                "Currency": "€"
              }},
              ...
              {{
                "Internal Number": "1",
                "Item Number": null,
                "Item Description": "Subtotal Excavating & filling",
                "Unit": null,
                "Quantity": null,
                "Rate": null,
                "Amount": "14230.00",
                "Currency": null
              }}
            ]
          }}
        ]
      }}
    ]
  }}
]

If no nested subsections:
[
  {{
    "Section Title": "1.1 Preliminaries",
    "Items": [
      {{
        "Internal Number": "0",
        "Item Number": "1.1.1.1",
        "Item Description": "Mobile tele-crane and driver",
        "Unit": "day",
        "Quantity": "1.00",
        "Rate": "350.00",
        "Amount": "350.00",
        "Currency": "£"
      }}
    ]
  }}
]

📌 Extraction Rules:

1. Section headers (e.g. "2.5 Excavating & filling") should be used as "Section Title".

2. Subsection headers (e.g. "2.5.1 Fillings") should be added as "Subsection Title" inside "Subsections".

3. Further nested headers (e.g. "2.5.1.1 Fillings obtained from excavated material") should be "Subsection Title" again inside further "Subsections" nesting.

4. A line is considered a **header** (Section/Subsection) if:
   - It contains a number pattern like 2.5.1.1 **and**
   - All of these fields are empty or null: Quantity, Unit, Rate, and Amount.
   ➤ Otherwise, treat it as a normal item.

5. Ensure item keys follow this **exact naming and order**:
"Internal Number"
"Item Number"  
"Item Description"  
"Unit"  
"Quantity"  
"Rate"  
"Amount"  
"Currency"
6. Add a unique "Internal Number" to each item (not headers or subsections), starting from 0, increasing by 1 regardless of its section/subsection position.
If a field is not available, set its value to null.

📌 Subtotal Rule:

If a subtotal row is present, it must:
- Be the **last item** in the section’s "Items" array.
- Have "Item Number" = null.
- "Item Description" must contain the word Subtotal and the name of the section.
- "Amount" must be present and not null.

Do **not** create a subtotal if:
- There's no keyword like Subtotal, S/Total, or Total.
- Or if the "Amount" is missing or empty.

📌 Output Rules:
- Only return a **valid JSON array**.
- Do not include any markdown, comments, or extra explanation.
- Do not wrap the JSON in code blocks (```json).
- Unescape newline characters (`\\n`) — Python will handle formatting.

EXTRACTED TEXT:
{extracted_text}

ONLY return the structured JSON in the described format.
"""
    return prompt


def call_gemini_return_json(prompt):
    """
    Call Google's Gemini API with a prompt and return the response as parsed JSON.
    
    This function sends a prompt to the Gemini 2.5 Flash model with deterministic
    settings (temperature=0) and attempts to parse the response as JSON. It handles
    the common case where Gemini wraps JSON responses in markdown code blocks.
    
    Args:
        prompt (str): The input prompt to send to the Gemini API
    
    Returns:
        dict: Parsed JSON response from Gemini, or error dictionary if parsing fails
              Error format: {"error": "...", "raw_response": "..."}
    
    Note:
        - Temperature is set to 0.0 for deterministic/consistent outputs
        - Automatically strips markdown code block formatting (```json...```)
        - Requires GEMINI_API_KEY to be set in environment or defined globally
    """
    # Configure API with authentication key
    api_key = api_key  # TODO: Should reference actual API key variable
    genai.configure(api_key=api_key)
    
    # Configure generation parameters for deterministic output
    generation_config = {
        "temperature": 0.0,  # Set temperature to 0 for deterministic output
        # Additional parameters can be added here: "top_p", "top_k", "max_output_tokens"
    }
    
    # Initialize the Gemini model with configuration
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config=generation_config)
    
    # Generate content from the model
    response = model.generate_content(prompt)
    raw_text_content = response.text  # Extract raw text from response
    
    # Clean the response by removing markdown JSON code block formatting
    cleaned_response = raw_text_content.strip().removeprefix('```json\n').removesuffix('\n```')
    
    try:
        # Attempt to parse the cleaned response as JSON
        import json
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        # Return error information if JSON parsing fails
        return {
            "error": "Response is not valid JSON", 
            "raw_response": cleaned_response  # Note: .text removed as cleaned_response is already a string
        }

