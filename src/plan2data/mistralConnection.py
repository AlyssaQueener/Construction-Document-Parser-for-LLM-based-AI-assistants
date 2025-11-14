
from mistralai import Mistral
import base64
import os
## Retrieve the API key from environment variables
api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
client = Mistral(api_key=api_key)


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

def call_mistral_for_titleblock_extraction_from_image(path):
    message = create_message_for_titleblock_extraction_from_image(path)
    chat_response = client.chat.complete(
        model = model,
        messages = message,
        response_format = {
            "type": "json_object",
        }
    )

    return chat_response.choices[0].message.content

def create_message_for_titleblock_extraction_from_image(path):
    base64_image = encode_image(path)
    text = create_titleblock_extraction_prompt()
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
    

def create_titleblock_extraction_prompt():
    prompt = f"""
Architectural Title Block Information Extraction

You are an expert at extracting structured information from architectural drawing title blocks in both German and English.

Your Task
Analyze the image of the architectural drawing and identify key metadata fields commonly found in architectural title blocks. Extract ONLY information that is explicitly present image.

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



