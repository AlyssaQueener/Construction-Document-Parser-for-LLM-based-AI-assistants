from mistralai import Mistral

def create_extraction_prompt_with_examples(extracted_text):
    """
    Enhanced prompt with examples for better extraction accuracy
    """
    prompt = f"""
You are an expert at extracting structured information from German architectural drawings and floorplans.

EXAMPLES OF WHAT TO LOOK FOR:
- Auftraggeber: "Bauherr: Max Mustermann", "Auftraggeber: Firma XYZ GmbH"
- Erstellungsdatum: "Datum: 15.03.2024", "gezeichnet: 12/23", "Erstellt am 01.02.2024"
- Planinhalt: "Grundriss EG", "Ansicht Süd", "Schnitt A-A", "Lageplan"
- Projektnummer: "Proj.-Nr.: 2024-15", "Vorhaben: V-123", "Projekt 2024/045"
- Maßstab: "M 1:100", "Maßstab 1:50", "1:200"
- Architekt: "Architekt: Schmidt & Partner", "Büro: Planungsgruppe Nord"

EXTRACTED TEXT:
{extracted_text}

Please extract the information following the same guidelines as the previous prompt, returning only valid JSON.

{{
    "Auftraggeber": "value or null",
    "Erstellungsdatum": "value or null",
    "Planinhalt": "value or null", 
    "Projektnummer": "value or null",
    "Maßstab": "value or null",
    "Architekt": "value or null"
}}
"""
    return prompt

def call_mistral_return_json(promt):        
    model = "mistral-small-latest"
    api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"

    client = Mistral(api_key=api_key)
    messages = [
        {
        "role": "user",
        "content": promt,
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
