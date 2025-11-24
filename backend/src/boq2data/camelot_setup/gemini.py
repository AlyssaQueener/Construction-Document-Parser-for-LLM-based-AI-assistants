import os
#import google.generativeai as genai
import json


#def make_gemini_easy_call(prompt_text="Hello, Gemini! How are you today?"):
#    """
#    Makes a simple call to the Google Gemini API using the GOOGLE_API_KEY
#    environment variable.
#    """
#    try:
#        # 1. Retrieve and configure API key from environment variable
#        api_key = os.environ["GOOGLE_API_KEY"]
#        genai.configure(api_key=api_key)
#        print("API Key configured from environment variable.")

        # 2. Initialize the Gemini-Pro model
     #   model = genai.GenerativeModel('gemini-2.5-flash')
      #  print(f"Sending prompt to Gemini: '{prompt_text}'")

        # 3. Make the generative call
       # response = model.generate_content(prompt_text)

        # 4. Print the generated text
        #print("\n--- Gemini's Response ---")
        #print(response.text)
        #print("-----------------------")

    #except KeyError:
    #    print("\nERROR: GOOGLE_API_KEY environment variable is not set.")
     #   print("Please set it before running this script.")
      #  print("For example (PowerShell): $env:GOOGLE_API_KEY=\"YOUR_API_KEY\"")
       # print("Or (Linux/macOS): export GOOGLE_API_KEY=\"YOUR_API_KEY\"")
    #except Exception as e:
     #   print(f"\nAN ERROR OCCURRED DURING GEMINI API CALL:")
      #  print(f"Error type: {type(e).__name__}")
       # print(f"Error details: {e}")
        #print("\nTroubleshooting tips:")
        #print("- Double-check your API key's validity on Google AI Studio.")
        #print("- Ensure you have an active internet connection.")
        #print("- Verify the 'gemini-pro' model is accessible with your key.")
        
def create_preproccesed_prompt(extracted_text):
    
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
  - sometimes there are subsection titles under the section titles they are called " Subsection Title" if present include them in the nested structure 
  - Each section should contain an `"Items"` list of the line items.
  - Include subtotals **as the last item** in the `Items` array of each section.

  📌 Rules to follow:

  Section headers (like "2.5.1 Fillings") should be used as "Section Title"..
  Subsection headers (like "2.5.1 Fillings obtained from excavated material" ) should be used as Subsection Title.. they can be idetified by their consecutive number or are underlined 
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

  - Do NOT group items under custom keys like "Category" or "Item" — only use "Section Title", if present "Subsection title" and "Items".
  - DO NOT include any introductory or explanatory text. ONLY output the JSON.**
  - **DO NOT wrap the JSON in markdown code blocks (e.g., ```json...```).**
  **Unescape the newline characters (`\n`).** The `json` library in Python will handle this automatically if you provide it with a clean string.

  Confidence Score
  Provide a confidence score (0.0 to 1.0) based on:
  - 1.0: 10+ fields found with clear, unambiguous values
  - 0.8-0.9: 7-9 fields found, values are clear
  - 0.6-0.7: 5-6 fields found, or some ambiguity in values
  - 0.4-0.5: 3-4 fields found, moderate ambiguity
  - 0.2-0.3: 1-2 fields found, significant ambiguity
  - 0.0-0.1: No fields clearly identified, text may not be a title block

  ✅ Output must be valid JSON — no extra text, markdown, or explanation.
          EXTRACTED TEXT:
          {extracted_text}
      ONLY return the structured JSON in the described format.

          

  📌 JSON Schema:
  ```json
  [{{"Section Title": "2.5.1 Fillings ",
    {{
      "Subsection Title": "2.5.1 Fillings obtained from excavated material",
      "Items": [
        {{
          "Item Number": "2.5.1.1.1",
          "Item Description": "Fill obtained from temporary spoil heaps to foundations, level compacted in max 150mm layers byhand >500mm thick",
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
    "confidence": 0.0
  }},
    ...
  ]"""

    return prompt 

def create_preprossed_prompt__mistral(extracted_text):
    """
    Constructs a detailed prompt for Mistral to extract structured,
    section-grouped information from a Bill of Quantities (BoQ).
    Includes subtotals and organizes items under section headers.
    """
    prompt = f"""
You are an expert system for extracting structured data from English or German Bill of Quantities (BoQs).

Your task:
- Extract item rows and organize them into a structured JSON OBJECT (not an array).
- Group each section under a key called "Section Title".
- If subsection titles exist under section titles, include them as "Subsection Title" in a nested structure.
- Each section/subsection should contain an "Items" list of line items.
- Include subtotals as the last item in the "Items" array of each section/subsection.

Rules to follow:
- Section headers (like "VIII SITE WORKS") should be used as "Section Title".
- Subsection headers should be used as "Subsection Title" if they exist.
- Ensure item keys follow this exact naming and order:
    "Item Number"
    "Item Description"
    "Unit"
    "Quantity"
    "Rate"
    "Amount"
    "Currency"
- If a subtotal row is present, it must:
  - Appear as the last object in the section's "Items" array
  - Set "Item Number" to null
  - Use "Subtotal [Section/Subsection name]" in "Item Description"
  - Set "Unit", "Quantity", and "Rate" to null
  - Include "Amount" and "Currency"
- Do NOT group items under custom keys like "Category" or "Item" — only use "Section Title", "Subsection Title" (if present), and "Items".

Confidence Score:
Provide a single confidence score (0.0 to 1.0) at the root level of the JSON output based on the overall extraction quality.

EXTRACTED TEXT:
{extracted_text}

CRITICAL - YOUR RESPONSE MUST FOLLOW THIS EXACT STRUCTURE:
{{
  "Sections": [
    {{
      "Section Title": "VIII SITE WORKS",
      "Subsections": [],
      "Items": [
        {{
          "Item Number": "1",
          "Item Description": "Stone Foundation (60 Cm Height)",
          "Unit": "m3",
          "Quantity": "50",
          "Rate": "45,000",
          "Amount": "2,250,000",
          "Currency": "USD"
        }},
        {{
          "Item Number": "7",
          "Item Description": "Retaining wall",
          "Unit": "m3",
          "Quantity": "81.2",
          "Rate": "60,000",
          "Amount": "4,872,000",
          "Currency": "USD"
        }}
      ]
    }}
  ],
  "confidence": 0.95
}}

IMPORTANT REMINDERS:
1. Your response MUST be a JSON OBJECT starting with {{ and ending with }}
2. Your response MUST NOT be a JSON ARRAY starting with [ and ending with ]
3. The top-level object MUST have exactly two keys: "Sections" and "confidence"
4. Do NOT include any markdown code blocks, explanations, or other text
5. Output ONLY the JSON object

Begin your response with {{
"""
    return prompt

"""def call_gemini_return_json(prompt):
    #api_key = os.environ["GOOGLE_API_KEY"]
    api_key = "AIzaSyD22tv_jw44Cnqp3J_9J-_1s85e5epop9s"
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
        return {"error": "Response is not valid JSON", "raw_response": cleaned_response.text}"""


