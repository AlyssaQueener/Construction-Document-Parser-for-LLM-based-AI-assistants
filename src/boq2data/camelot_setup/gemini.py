import os
import google.generativeai as genai
import json


def make_gemini_easy_call(prompt_text="Hello, Gemini! How are you today?"):
    """
    Makes a simple call to the Google Gemini API using the GOOGLE_API_KEY
    environment variable.
    """
    try:
        # 1. Retrieve and configure API key from environment variable
        api_key = os.environ["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        print("API Key configured from environment variable.")

        # 2. Initialize the Gemini-Pro model
        model = genai.GenerativeModel('gemini-2.5-flash')
        print(f"Sending prompt to Gemini: '{prompt_text}'")

        # 3. Make the generative call
        response = model.generate_content(prompt_text)

        # 4. Print the generated text
        print("\n--- Gemini's Response ---")
        print(response.text)
        print("-----------------------")

    except KeyError:
        print("\nERROR: GOOGLE_API_KEY environment variable is not set.")
        print("Please set it before running this script.")
        print("For example (PowerShell): $env:GOOGLE_API_KEY=\"YOUR_API_KEY\"")
        print("Or (Linux/macOS): export GOOGLE_API_KEY=\"YOUR_API_KEY\"")
    except Exception as e:
        print(f"\nAN ERROR OCCURRED DURING GEMINI API CALL:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e}")
        print("\nTroubleshooting tips:")
        print("- Double-check your API key's validity on Google AI Studio.")
        print("- Ensure you have an active internet connection.")
        print("- Verify the 'gemini-pro' model is accessible with your key.")
        
def create_extraction_prompt(extracted_text):
    
    """
    Constructs a detailed prompt for Gemini to extract structured,
    section-grouped information from a Bill of Quantities (BoQ).
    Includes subtotals and organizes items under section headers.
    """
    prompt = f"""
You are an expert system for extracting structured data from English or German Bill of Quantities (BoQs).

🔧 Your task:
- Extract item rows and organize them into a JSON array.
- Group each section under a key called `"Section Title"`.
- Each section should contain an `"Items"` list of the line items.
- Include subtotals **as the last item** in the `Items` array of each section.

📌 JSON Schema:
```json
[
  {{
    "Section Title": "1 PRELIMINARY WORKS",
    "Items": [
      {{
        "Item Number": "1.1",
        "Item Description": "Excavation for foundations",
        "Unit": "m³",
        "Quantity": "150",
        "Rate": "25.00",
        "Amount": "3750.00",
        "Currency": "€"
      }},
      ...
      {{
        "Item Number": null,
        "Item Description": "Subtotal",
        "Unit": null,
        "Quantity": null,
        "Rate": null,
        "Amount": "14230.00",
        "Currency": "€"
      }}
    ]
  }},
  ...
]
📌 Rules to follow:

Section headers (like "1 PRELIMINARY WORKS", "2 MASONRY") should be used as "Section Title"..
Ensure item keys follow this exact naming and order:

    "Item Number"
    "Item Description"
    "Unit"
    "Quantity"
    "Rate"
    "Amount"
    "Currency"

If the subtotal row is present, it must:

- Appear as the last object in the section’s "Items" array.
- Set "Item Number" to null.
- Use "Subtotal" of "Section header" in "Item Description". e.g Subtotal Prelimanry works

- Do NOT group items under custom keys like "Category" or "Item" — only use "Section Title" and "Items".
- DO NOT include any introductory or explanatory text. ONLY output the JSON.**
- **DO NOT wrap the JSON in markdown code blocks (e.g., ```json...```).**
**Unescape the newline characters (`\n`).** The `json` library in Python will handle this automatically if you provide it with a clean string.

✅ Output must be valid JSON — no extra text, markdown, or explanation.
        EXTRACTED TEXT:
        {extracted_text}
     ONLY return the structured JSON in the described format.
"""
        
    return prompt 

def call_gemini_return_json(prompt):
    api_key = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    generation_config = {
        "temperature": 0.0,  # Set temperature to 0 for deterministic output
        # You can add other parameters here if needed, e.g., "top_p", "top_k", "max_output_tokens"
    }
    model = genai.GenerativeModel('gemini-2.5-flash',generation_config=generation_config)
     # Define the generation configuration

    response = model.generate_content(prompt)
    raw_text_content = response.text # so that the ouput is just the 
        
     # Now apply string methods to the raw_text_content
    cleaned_response = raw_text_content.strip().removeprefix('```json\n').removesuffix('\n```')
    
    try:
        # Attempt to parse the response as JSON
        import json
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        return {"error": "Response is not valid JSON", "raw_response": cleaned_response.text}


