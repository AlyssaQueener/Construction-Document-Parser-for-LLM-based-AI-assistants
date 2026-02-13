import  google.generativeai as genai
        
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