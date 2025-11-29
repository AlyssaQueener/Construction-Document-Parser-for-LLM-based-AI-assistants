
from mistralai import Mistral
import base64

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
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
######################Titleblock #######################################
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
################################# Neigbouring and Connected rooms ################
#######################
def call_mistral_for_room_adjacency_extraction(path):
    """Extract only room adjacency information from floor plan image"""
    message = create_message_for_room_adjacency_extraction(path)
    chat_response = client.chat.complete(
        model = model,
        messages = message,
        response_format = {
            "type": "json_object",
        }
    )
    return chat_response.choices[0].message.content

def create_message_for_room_adjacency_extraction(path):
    base64_data, file_type, media_type = encode_file(path)
    text = create_room_adjacency_extraction_prompt()
    # Determine content type based on file type
      # Build the file content dynamically
    if file_type == 'pdf':
        file_content = {
            "type": "document_url",
            "document_url": f"data:{media_type};base64,{base64_data}"
        }
    else:  # image
        file_content = {
            "type": "image_url",
            "image_url": f"data:{media_type};base64,{base64_data}"
        }
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                file_content  # Insert the dynamically built dictionary
            ]
        }
    ]
    return messages

################################## Full Floorplan Metadata ####################
def call_mistral_for_floorplan_extraction_from_image(path):
    """Extract both titleblock and room adjacency information from floor plan image"""
    message = create_message_for_full_floorplan_extraction(path)
    chat_response = client.chat.complete(
        model = model,
        messages = message,
        response_format = {
            "type": "json_object",
        }
    )
    return chat_response.choices[0].message.content

def create_message_for_full_floorplan_extraction(path):
    text = create_full_floorplan_extraction_prompt()
    base64_data, file_type, media_type = encode_file(path)
    
    
    # Build the file content dynamically
    if file_type == 'pdf':
        file_content = {
            "type": "document_url",
            "document_url": f"data:{media_type};base64,{base64_data}"
        }
    else:  # image
        file_content = {
            "type": "image_url",
            "image_url": f"data:{media_type};base64,{base64_data}"
        }
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                file_content  # Insert the dynamically built dictionary
            ]
        }
    ]
    return messages

###################### ENCODE IMPORT FILES ########################################
def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def encode_pdf(pdf_path):
    """Encode the PDF to base64."""
    try:
        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {pdf_path} was not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_file_type(file_path):
    """Determine if file is an image or PDF based on extension."""
    extension = file_path.lower().split('.')[-1]
    if extension in ['pdf']:
        return 'pdf'
    elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        return 'image'
    else:
        return 'unknown'

def encode_file(file_path):
    """
    Encode either an image or PDF to base64.
    Returns tuple: (base64_data, file_type, media_type)
    """
    file_type = get_file_type(file_path)
    
    if file_type == 'pdf':
        base64_data = encode_pdf(file_path)
        media_type = "application/pdf"
    elif file_type == 'image':
        base64_data = encode_image(file_path)
        media_type = "image/jpeg"
    else:
        raise ValueError(f"Unsupported file type for {file_path}. Supported types: PDF, JPG, JPEG, PNG, GIF, BMP, WEBP")
    
    if base64_data is None:
        raise ValueError(f"Failed to encode file: {file_path}")
    
    return base64_data, file_type, media_type

################## Prompt Titleblock ################################
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

##################################### Neighbouring connected Rooms ############
def create_room_adjacency_extraction_prompt():
    """Standalone prompt for room adjacency extraction only"""
    prompt = f"""
Architectural Floor Plan Room Adjacency Extraction

You are an expert at analyzing architectural floor plans and identifying spatial relationships between rooms.

Your Task
Analyze the floor plan image and extract room adjacency relationships - which rooms are next to or connected to each other.

Room Identification:
- Look for room labels in the floor plan
- Common German room types: KÜCHE, WOHN/ESSZIMMER, WOHNZIMMER, ESSZIMMER, SCHLAFZIMMER, BADEZIMMER, BAD, WC, DIELE, FLUR, ABSTELL ZIMMER, ABSTELLRAUM, HWR (Hauswirtschaftsraum), GÄSTEZIMMER, ARBEITSZIMMER, KINDERZIMMER, TERRASSE, BALKON, LOGGIA
- Common English room types: KITCHEN, LIVING ROOM, DINING ROOM, BEDROOM, BATHROOM, HALLWAY, CORRIDOR, STORAGE, UTILITY ROOM, GUEST ROOM, OFFICE, CHILDREN'S ROOM, TERRACE, BALCONY
- Preserve exact room names as they appear in the plan (including spaces, slashes, capitalization)

Adjacency Types:

1. NEIGHBORING ROOMS (neighboringRooms):
Rooms that share a wall or boundary, regardless of whether there's a door between them.
This includes:
- Rooms separated by walls with doors
- Rooms separated by walls without doors
- Rooms separated by windows or glass partitions
- Outdoor spaces (terraces, balconies) adjacent to interior rooms

2. CONNECTED ROOMS (connectedRooms):
Rooms that have a direct physical connection through a doorway or opening.
This includes:
- Rooms with doors between them
- Rooms with open passages
- Rooms with archways
This excludes:
- Rooms only separated by windows
- Rooms only sharing walls without doorways

Adjacency Rules:
- List adjacencies from EACH room's perspective
- If Room A is adjacent to Room B, then Room B must also list Room A
- Sort adjacent rooms alphabetically within each room's list
- Include ALL adjacent rooms, not just the main connections
- Be consistent: if you identify a connection in one direction, include it in both directions

Output Format
Return ONLY valid JSON with no additional text:

{{
    "neighboringRooms": {{
        "ROOM_NAME_1": ["ADJACENT_ROOM_1", "ADJACENT_ROOM_2"],
        "ROOM_NAME_2": ["ADJACENT_ROOM_1", "ADJACENT_ROOM_3"]
    }},
    "connectedRooms": {{
        "ROOM_NAME_1": ["CONNECTED_ROOM_1", "CONNECTED_ROOM_2"],
        "ROOM_NAME_2": ["CONNECTED_ROOM_1"]
    }},
    "confidence": 0.0

}}

Confidence Score (0.0-1.0):
- 1.0: All rooms clearly labeled, all adjacencies clearly visible
- 0.8-0.9: Most rooms labeled, adjacencies clear
- 0.6-0.7: Some rooms unlabeled or adjacencies ambiguous
- 0.4-0.5: Many rooms unclear or layout complex
- 0.2-0.3: Very few rooms identifiable
- 0.0-0.1: Cannot determine room layout

Instructions:
- Include only rooms that are clearly labeled in the floor plan
- Preserve original language and exact naming (including spaces, capitalization, special characters)
- Be thorough: include ALL adjacent rooms for each room
- Verify reciprocal relationships: if A lists B, then B must list A
- Sort adjacent rooms alphabetically within each room's list

Extract the information now.
"""
    return prompt

###################### Full Flooplan AI #####################################
def create_full_floorplan_extraction_prompt():
    """Combined prompt for titleblock and room adjacency extraction"""
    prompt = f"""
Architectural Floor Plan Information Extraction

You are an expert at extracting structured information from architectural floor plans in both German and English.

Your Task
Analyze the floor plan image and extract:
1. Title block metadata (project information and plan details)
2. Room adjacency relationships (which rooms are next to or connected to each other)

PART 1: TITLE BLOCK EXTRACTION

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

4. Author / Drawn By
German terms: gezeichnet, gez., Zeichner, Bearbeiter, erstellt von
English terms: Drawn by, Author, Drafted by, Prepared by

5. Client
German terms: Bauherr, Auftraggeber, Bauherrschaft
English terms: Client, Commissioned by, Owner

6. Architect / Architectural Firm
German terms: Architekt, Architekturbüro, Planungsbüro, Büro
English terms: Architect, Architectural Office, Firm, Designer

7. Engineers (Structural, MEP, etc.)
German terms: Ingenieur, Tragwerksplaner, Statiker, Fachplaner, TGA-Planer
English terms: Engineer, Structural Engineer, MEP Engineer, Consultant

8. Year of Completion / Construction Year
German terms: Fertigstellung, Baujahr, Fertigstellungsjahr
English terms: Year of Completion, Construction Year, Completion Date
Format: Return as YYYY format

9. Approval Date / Permit Date
German terms: Genehmigungsdatum, Baugenehmigung, genehmigt am
English terms: Approval Date, Permit Date, Approved on
Format: Return in ISO format (YYYY-MM-DD) when possible

PLAN METADATA:

10. Plan Type / Drawing Type
German terms: Grundriss, Ansicht, Schnitt, Lageplan, Detailplan, Planart
English terms: Floor Plan, Elevation, Section, Site Plan, Detail, Drawing Type

11. Plan Format / Sheet Size
German terms: Format, Blattformat, Plangröße
English terms: Format, Sheet Size, Paper Size
Standardize to: A0, A1, A2, A3, A4, or custom dimensions if specified

12. Scale
German terms: Maßstab, M
English terms: Scale
Format: Standardize to "1:X" format (e.g., "1:100")

13. Projection Method
German terms: Darstellung, Projektion, Ansichtsart
English terms: Projection, View Type, Representation

PART 2: ROOM ADJACENCY EXTRACTION

Analyze the floor plan layout and identify all rooms and their spatial relationships.

Room Identification:
- Look for room labels in the floor plan
- Common German room types: KÜCHE, WOHN/ESSZIMMER, WOHNZIMMER, ESSZIMMER, SCHLAFZIMMER, BADEZIMMER, BAD, WC, DIELE, FLUR, ABSTELL ZIMMER, ABSTELLRAUM, HWR (Hauswirtschaftsraum), GÄSTEZIMMER, ARBEITSZIMMER, KINDERZIMMER, TERRASSE, BALKON, LOGGIA
- Common English room types: KITCHEN, LIVING ROOM, DINING ROOM, BEDROOM, BATHROOM, HALLWAY, CORRIDOR, STORAGE, UTILITY ROOM, GUEST ROOM, OFFICE, CHILDREN'S ROOM, TERRACE, BALCONY
- Preserve exact room names as they appear in the plan (including spaces, slashes, capitalization)

Adjacency Types:

1. NEIGHBORING ROOMS (neighboringRooms):
Rooms that share a wall or boundary, regardless of whether there's a door between them.
This includes:
- Rooms separated by walls with doors
- Rooms separated by walls without doors
- Rooms separated by windows or glass partitions
- Outdoor spaces (terraces, balconies) adjacent to interior rooms

2. CONNECTED ROOMS (connectedRooms):
Rooms that have a direct physical connection through a doorway or opening.
This includes:
- Rooms with doors between them
- Rooms with open passages
- Rooms with archways
This excludes:
- Rooms only separated by windows
- Rooms only sharing walls without doorways

Adjacency Rules:
- List adjacencies from EACH room's perspective
- If Room A is adjacent to Room B, then Room B must also list Room A
- Sort adjacent rooms alphabetically within each room's list
- Include ALL adjacent rooms, not just the main connections
- Be consistent: if you identify a connection in one direction, include it in both directions

Output Format
Return ONLY valid JSON with no additional text:

{{
    "titleBlock": {{
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
    }},
    "roomAdjacency": {{
        "neighboringRooms": {{
            "ROOM_NAME_1": ["ADJACENT_ROOM_1", "ADJACENT_ROOM_2"],
            "ROOM_NAME_2": ["ADJACENT_ROOM_1", "ADJACENT_ROOM_3"]
        }},
        "connectedRooms": {{
            "ROOM_NAME_1": ["CONNECTED_ROOM_1", "CONNECTED_ROOM_2"],
            "ROOM_NAME_2": ["CONNECTED_ROOM_1"]
        }},
        "confidence": 0.0
    }}
}}

Confidence Scores:
- Title Block Confidence (0.0-1.0): Based on number of fields found
  - 1.0: 10+ fields found with clear values
  - 0.8-0.9: 7-9 fields found
  - 0.6-0.7: 5-6 fields found
  - 0.4-0.5: 3-4 fields found
  - 0.2-0.3: 1-2 fields found
  - 0.0-0.1: No fields identified

- Room Adjacency Confidence (0.0-1.0): Based on clarity of room layout
  - 1.0: All rooms clearly labeled, all adjacencies clearly visible
  - 0.8-0.9: Most rooms labeled, adjacencies clear
  - 0.6-0.7: Some rooms unlabeled or adjacencies ambiguous
  - 0.4-0.5: Many rooms unclear or layout complex
  - 0.2-0.3: Very few rooms identifiable
  - 0.0-0.1: Cannot determine room layout

Instructions:
- Extract only explicitly present information - do not infer or guess
- For title block: if a field is not found, return null
- For room adjacency: include only rooms that are clearly labeled
- Preserve original language and exact naming (including spaces, capitalization, special characters)
- Clean extracted values: remove labels/prefixes
- Be thorough: include ALL adjacent rooms for each room
- Verify reciprocal relationships: if A lists B, then B must list A

Extract the information now.
"""
    return prompt

