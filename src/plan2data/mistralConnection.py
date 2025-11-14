
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

Please extract the relevant information based on the examples above. Keep in mind that not every title block necesseraly contains all the information listed above.
Based on the extracted text, please also return an confident value in range 0-1 (like 0.4,0.8,etc) rating wether the extraction was succesful or not.
Return only valid JSON with the following English keys:

{{
    "client": "value or null",
    "creation_date": "value or null",
    "drawing_name/ plan type": "value or null",
    "project_name": "value or null",
    "location": "value or null",
    "scale": "value or null",
    "architect": "value or null",
    "confident_value": "value
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
    message = create_detailed_title_block_extraction_promt_with_confidence_value(text_title_block)
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

def create_title_block_extraction_promt_with_confidence_value(extracted_text):
    prompt = f"""
Architectural Title Block Information Extraction
You are an expert at extracting structured information from architectural drawing title blocks in both German and English.
Your Task
Analyze the extracted text below and identify key metadata fields commonly found in architectural title blocks. Extract ONLY information that is explicitly present in the text.
Fields to Extract
1. Client
German terms: Bauherr, Auftraggeber, Bauherrschaft
English terms: Client, Commissioned by, Owner
Examples: "Bauherr: Max Mustermann", "Client: John Smith", "Auftraggeber: Firma XYZ GmbH"
2. Creation Date
German terms: Datum, gezeichnet, Erstellt am, gez.
English terms: Date, Drawn on, Created
Examples: "Datum: 15.03.2024", "gezeichnet: 12/23", "Date: February 1, 2024"
Format: Return in ISO format (YYYY-MM-DD) when possible, or as found if ambiguous
3. Drawing Name/Type
German terms: Grundriss, Ansicht, Schnitt, Lageplan, Detailplan
English terms: Floor Plan, Elevation, Section, Site Plan, Detail
Examples: "Grundriss EG", "South Elevation", "Schnitt A-A"
4. Project Name/Number
German terms: Projekt, Vorhaben, Proj.-Nr., Objekt
English terms: Project, Job Number, Project No.
Examples: "Neubau Amalienstraße", "Proj.-Nr.: 2024-15", "Project No.: V-123"
5. Location
Examples: "80686 München", "Munich, Germany", "Amalienstraße 45, München"
Note: Include full address if available
6. Scale
German terms: Maßstab, M
English terms: Scale
Examples: "M 1:100", "Maßstab 1:50", "1:200", "Scale: 1:100"
Format: Standardize to "1:X" format (e.g., "1:100")
7. Architect/Firm
German terms: Architekt, Büro, Planer, Planungsbüro
English terms: Architect, Office, Firm, Designer
Examples: "Architekt: Schmidt & Partner", "Office: North Design Group"
Instructions

Extract only explicitly stated information - do not infer or guess
If a field is not found, return null for that field
If multiple values exist for a field (e.g., multiple dates), return the most prominent one
Preserve original language of extracted values (don't translate)
Clean extracted values: remove labels/prefixes (e.g., "Bauherr: Max" → "Max")

Confidence Score
Provide a confidence score (0.0 to 1.0) based on:

1.0: All 7 fields found with clear, unambiguous values
0.8-0.9: 4-6 fields found, values are clear
0.5-0.7: 3-4 fields found, or some ambiguity in values
0.3-0.4: 1-2 fields found, significant ambiguity
0.0-0.2: No fields clearly identified, text may not be a title block

Output Format
Return ONLY valid JSON with no additional text:
{{
    "client": "value or null",
    "creation_date": "value or null",
    "drawing_name": "value or null",
    "project_name": "value or null",
    "location": "value or null",
    "scale": "value or null",
    "architect": "value or null",
    "confidence": 0.0
}}
Extracted Text to Analyze
{extracted_text}
Extract the information now.
"""
    return prompt

def create_detailed_title_block_extraction_promt_with_confidence_value(extracted_text):
    prompt = f"""
Architectural Title Block Information Extraction

You are an expert at extracting structured information from architectural drawing title blocks in both German and English.

Your Task
Analyze the extracted text below and identify key metadata fields commonly found in architectural title blocks. Extract ONLY information that is explicitly present in the text.

Fields to Extract

PROJECT INFORMATION:

1. Project ID / Number
German terms: Projekt-Nr., Proj.-Nr., Projektnummer, Vorhaben-Nr., Objekt-Nr.
English terms: Project ID, Project No., Job Number, Project Number
Examples: "Proj.-Nr.: 2024-15", "Project No.: V-123", "Job #: 2024-ABC"

2. Project Name
German terms: Projekt, Vorhaben, Projektname, Objekt, Bauvorhaben
English terms: Project, Project Name, Development, Building Project
Examples: "Neubau Amalienstraße", "Residential Complex Munich", "Office Tower Project"

3. Location / Address
German terms: Standort, Ort, Adresse, Lage
English terms: Location, Address, Site, Place
Examples: "80686 München", "Munich, Germany", "Amalienstraße 45, München"
Note: Include full address if available (street, postal code, city, country)

4. Author / Drawn By
German terms: gezeichnet, gez., Zeichner, Bearbeiter, erstellt von
English terms: Drawn by, Author, Drafted by, Prepared by
Examples: "gez.: M. Schmidt", "Drawn by: John Smith", "Bearbeiter: Anna Müller"

5. Client
German terms: Bauherr, Auftraggeber, Bauherrschaft
English terms: Client, Commissioned by, Owner
Examples: "Bauherr: Max Mustermann", "Client: John Smith", "Auftraggeber: Firma XYZ GmbH"

6. Architect / Architectural Firm
German terms: Architekt, Architekturbüro, Planungsbüro, Büro
English terms: Architect, Architectural Office, Firm, Designer
Examples: "Architekt: Schmidt & Partner", "Office: North Design Group", "Architekturbüro Müller"

7. Engineers (Structural, MEP, etc.)
German terms: Ingenieur, Tragwerksplaner, Statiker, Fachplaner, TGA-Planer
English terms: Engineer, Structural Engineer, MEP Engineer, Consultant
Examples: "Statiker: Ingenieurbüro Wagner", "MEP: TechConsult GmbH"
Note: Extract multiple engineers if present, specify type if mentioned

8. Year of Completion / Construction Year
German terms: Fertigstellung, Baujahr, Fertigstellungsjahr
English terms: Year of Completion, Construction Year, Completion Date
Examples: "Fertigstellung: 2025", "Completion: 2024"
Format: Return as YYYY format

9. Approval Date / Permit Date
German terms: Genehmigungsdatum, Baugenehmigung, genehmigt am
English terms: Approval Date, Permit Date, Approved on
Examples: "Baugenehmigung: 15.03.2024", "Approved: 02/2024"
Format: Return in ISO format (YYYY-MM-DD) when possible

PLAN METADATA:

10. Plan Type / Drawing Type
German terms: Grundriss, Ansicht, Schnitt, Lageplan, Detailplan, Planart
English terms: Floor Plan, Elevation, Section, Site Plan, Detail, Drawing Type
Examples: "Grundriss EG", "South Elevation", "Schnitt A-A", "Site Plan"

11. Plan Format / Sheet Size
German terms: Format, Blattformat, Plangröße
English terms: Format, Sheet Size, Paper Size
Examples: "A1", "A0", "Format: A3", "Sheet Size: 841×594mm"
Standardize to: A0, A1, A2, A3, A4, or custom dimensions if specified

12. Scale
German terms: Maßstab, M
English terms: Scale
Examples: "M 1:100", "Maßstab 1:50", "1:200", "Scale: 1:100"
Format: Standardize to "1:X" format (e.g., "1:100")

13. Projection Method
German terms: Darstellung, Projektion, Ansichtsart
English terms: Projection, View Type, Representation
Examples: "Isometrisch", "Orthogonal", "Perspektivisch", "Isometric", "Orthographic"

Instructions
- Extract only explicitly stated information - do not infer or guess
- If a field is not found, return null for that field
- If multiple values exist for a field (e.g., multiple engineers), include all in an array
- Preserve original language of extracted values (don't translate)
- Clean extracted values: remove labels/prefixes (e.g., "Bauherr: Max" → "Max")
- For dates, prioritize ISO format (YYYY-MM-DD) but preserve original format if conversion is ambiguous
- For engineers, create an array even if only one is found

Confidence Score
Provide a confidence score (0.0 to 1.0) based on:
- 1.0: 10+ fields found with clear, unambiguous values
- 0.8-0.9: 7-9 fields found, values are clear
- 0.6-0.7: 5-6 fields found, or some ambiguity in values
- 0.4-0.5: 3-4 fields found, moderate ambiguity
- 0.2-0.3: 1-2 fields found, significant ambiguity
- 0.0-0.1: No fields clearly identified, text may not be a title block

Output Format
Return ONLY valid JSON with no additional text:

{{
    "projectInfo": {{
        "projectId": "value or null",
        "projectName": "value or null",
        "location": "value or null",
        "author": "value or null",
        "stakeholders": {{
            "client": "value or null",
            "architect": "value or null",
            "engineers": ["value1", "value2"] or null
        }},
        "timeline": {{
            "yearOfCompletion": "value or null",
            "approvalDate": "value or null"
        }}
    }},
    "planMetadata": {{
        "planType": "value or null",
        "planFormat": "value or null",
        "scale": "value or null",
        "projectionMethod": "value or null"
    }},
    "confidence": 0.0
}}

Extracted Text to Analyze
{extracted_text}

Extract the information now.
"""
    return prompt



