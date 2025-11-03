from mistralai import Mistral
import base64

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
client = Mistral(api_key=api_key)


def create_content_extraction_promt(extracted_text):
    """
    Enhanced prompt with examples for extracting structured data from architectural drawings in German and English.
    """
    prompt = f"""
You are an expert at extracting structured information from architectural drawings and floorplans in both German and English.

EXAMPLES OF WHAT TO LOOK FOR:
- Client: "Bauherr: Max Mustermann", "Auftraggeber: Firma XYZ GmbH", "Client: John Smith", "Commissioned by: ABC Ltd."
- Creation Date: "Datum: 15.03.2024", "gezeichnet: 12/23", "Erstellt am 01.02.2024", "Drawn on: 03/10/2024", "Date: February 1, 2024"
- Drawing Name: "Grundriss EG", "Ansicht Süd", "Schnitt A-A", "Lageplan", "Floor Plan Ground Floor", "South Elevation", "Section A-A", "Site Plan"
- Project Name: "Neubau Amalienstraße", "Proj.-Nr.: 2024-15", "Vorhaben: V-123", "Projekt 2024/045", "Project No.: 2024-15", "Job Number: V-123"
- Location:     "80686 München", "Munich, Germany"
- Scale: "M 1:100", "Maßstab 1:50", "1:200", "Scale: 1:100"
- Architect: "Architekt: Schmidt & Partner", "Büro: Planungsgruppe Nord", "Architect: Smith & Partners", "Office: North Design Group"

EXTRACTED TEXT:
{extracted_text}

Please extract the relevant information based on the examples above. Return only valid JSON with the following English keys:

{{
    "client": "value or null",
    "creation_date": "value or null",
    "drawing_name/ plan type": "value or null",
    "project_name": "value or null",
    "location": "value or null",
    "scale": "value or null",
    "architect": "value or null"
}}
"""
    return prompt

def create_content_extraction_promt_only_german(extracted_text):
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
    "Architekt": "value or null",
}}
"""
    return prompt

def call_mistral_for_content_extraction(text_title_block):
    message = create_content_extraction_promt(text_title_block)
    messages = [
        {
        "role": "user",
        "content": message,
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


def call_mistral_for_titleblock_location(path):
    message = create_message_for_titleblock_extraction(path)
    chat_response = client.chat.complete(
        model = model,
        messages = message,
        response_format = {
            "type": "json_object",
        }
    )

    return chat_response.choices[0].message.content

def create_message_for_titleblock_extraction(path):
    base64_image = encode_image(path)
    text = create_titleblock_localization_prompt()
    messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": text
            },
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{base64_image}"
            }
        ]
    }
]
    return messages

def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:  # Added general exception handling
        print(f"Error: {e}")
        return None
def create_titleblock_localization_prompt():
    prompt = """
You are an expert in identifying and localizing the titleblock area in German architectural drawings and floorplans.

The titleblock typically contains metadata such as:

- Auftraggeber (Client): e.g., "Bauherr: Max Mustermann", "Auftraggeber: Firma XYZ GmbH"
- Erstellungsdatum (Creation Date): e.g., "Datum: 15.03.2024", "gezeichnet: 12/23", "Erstellt am 01.02.2024"
- Planinhalt (Drawing Content): e.g., "Grundriss EG", "Ansicht Süd", "Schnitt A-A", "Lageplan"
- Projektnummer (Project Number): e.g., "Proj.-Nr.: 2024-15", "Vorhaben: V-123", "Projekt 2024/045"
- Maßstab (Scale): e.g., "M 1:100", "Maßstab 1:50", "1:200"
- Architekt (Architect): e.g., "Architekt: Schmidt & Partner", "Büro: Planungsgruppe Nord"

Localization is defined as the area of the image (in decimal percentages) where the titleblock is located, based on image width and height.
The coordinate origin is the lower left corner of the image.
Your task is to return the horizontal location as well as the vertical location of the title block
by identifying as decimal percentag value of the right/ and left borders of the titleblock in regard to the image width
and lower/upper borders in regard to image height

Return the localization in the following JSON format:

{
  "Horizontal location": {
    "From": "0.0-1.0",
    "To": "0.0-1.0"
  },
  "Vertical location": {
    "From": "0.0-1.0",
    "To": "0.0-1.0"
  }
}
Example Values
"""
    return prompt
