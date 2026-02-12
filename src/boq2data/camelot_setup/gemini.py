import os
import google.generativeai as genai
import json

api_key = "AIzaSyD22tv_jw44Cnqp3J_9J-_1s85e5epop9s"
def make_gemini_easy_call(prompt_text="Hello, Gemini! How are you today?"):
    """
    Makes a simple call to the Google Gemini API using the GOOGLE_API_KEY
    environment variable.
    """
    try:
        # 1. Retrieve and configure API key from environment variable
        api_key = api_key
        #os.environ["GOOGLE_API_KEY"]
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

def create_preprocessed_prompt(extracted_text):
    """
    Constructs a detailed prompt for Gemini to extract structured,
    section-grouped information from a Bill of Quantities (BoQ).
    Includes subtotals and organizes items under section headers.
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
    #api_key = os.environ["GOOGLE_API_KEY"]
    api_key = api_key
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


