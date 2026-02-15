
import json
from mistralai import Mistral
import base64
import time

# ==================== API CONFIGURATION ====================

## Retrieve the API key from environment variables
# api_key = os.environ["MISTRAL_API_KEY"]

# Mistral API configuration
model = "mistral-small-2503"  # Model version for API calls
api_key = "your api key" 
client = Mistral(api_key=api_key)


# ==================== TITLE BLOCK EXTRACTION (TEXT-BASED) ====================

def call_mistral_for_content_extraction(text_title_block):
    """
    Extract title block information from extracted text using Mistral AI.
    
    This function is used when text has already been extracted from the PDF
    and we want to parse it for structured title block information.
    
    Args:
        text_title_block (str): Extracted text from title block region
    
    Returns:
        str: JSON string containing structured title block data with confidence score
    
    Example:
        >>> text = "Projekt-Nr.: 2024-15\\nBauherr: Max Mustermann\\n..."
        >>> result = call_mistral_for_content_extraction(text)
        >>> data = json.loads(result)
        >>> print(data['projectInfo']['projectId'])
    """
    # Create detailed prompt with the extracted text
    message = create_detailed_title_block_extraction_promt_with_confidence_value(text_title_block)
    
    # Format for Mistral API
    messages = [
        {
            "role": "user",
            "content": message,
        }
    ]
    
    # Call Mistral API with JSON response format
    chat_response = client.chat.complete(
        model=model,
        messages=messages,
        response_format={
            "type": "json_object",
        }
    )
    
    response = chat_response.choices[0].message.content
    return response


# ==================== TITLE BLOCK EXTRACTION (IMAGE-BASED) ====================

def call_mistral_for_titleblock_extraction_from_image(path):
    """
    Extract title block information directly from floor plan image using Mistral Vision.
    
    Uses Mistral's vision model to analyze the image and extract structured
    title block metadata without requiring prior text extraction.
    
    Args:
        path (str): Path to floor plan image or PDF file
    
    Returns:
        str: JSON string containing structured title block data with confidence score
    
    Note:
        This method is more robust than text-based extraction as it can handle
        title blocks with complex layouts, tables, or embedded graphics.
    """
    # Create message with image
    message = create_message_for_titleblock_extraction_from_image(path)
    
    # Call Mistral Vision API
    chat_response = client.chat.complete(
        model=model,
        messages=message,
        response_format={
            "type": "json_object",
        }
    )

    return chat_response.choices[0].message.content


def create_message_for_titleblock_extraction_from_image(path):
    """
    Create Mistral API message structure for title block extraction from image.
    
    Args:
        path (str): Path to image file
    
    Returns:
        list: Formatted message array for Mistral API containing text prompt and image
    """
    # Encode image to base64
    base64_image = encode_image(path)
    
    # Get extraction prompt
    text = create_titleblock_extraction_prompt()
    
    # Build message structure with image
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


# ==================== ROOM ADJACENCY EXTRACTION ====================

def call_mistral_for_room_adjacency_extraction(path):
    """
    Extract room adjacency and connectivity information from floor plan.
    
    Analyzes floor plan to identify:
    - Neighboring rooms (share a wall/boundary)
    - Connected rooms (have a doorway/opening between them)
    
    Args:
        path (str): Path to floor plan image or PDF file
    
    Returns:
        str: JSON string containing:
             {
                 "neighboringRooms": {...},
                 "connectedRooms": {...},
                 "confidence": float
             }
    
    Example:
        >>> result = call_mistral_for_room_adjacency_extraction('floorplan.pdf')
        >>> data = json.loads(result)
        >>> print(data['neighboringRooms']['KÜCHE'])
        ['WOHNZIMMER', 'FLUR']
    """
    # Create message with file (handles both images and PDFs)
    message = create_message_for_room_adjacency_extraction(path)
    
    # Call Mistral API
    chat_response = client.chat.complete(
        model=model,
        messages=message,
        response_format={
            "type": "json_object",
        }
    )
    return chat_response.choices[0].message.content


def create_message_for_room_adjacency_extraction(path):
    """
    Create Mistral API message for room adjacency extraction.
    
    Handles both image and PDF files, automatically detecting file type
    and formatting appropriately for Mistral API.
    
    Args:
        path (str): Path to floor plan file (image or PDF)
    
    Returns:
        list: Formatted message array for Mistral API
    """
    # Encode file and determine type
    base64_data, file_type, media_type = encode_file(path)
    
    # Get extraction prompt
    text = create_room_adjacency_extraction_prompt()
    
    # Build file content based on type
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
    
    # Build message structure
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                file_content  # Dynamically inserted based on file type
            ]
        }
    ]
    return messages


# ==================== VORONOI ROOM EXTRACTION ====================

def call_mistral_for_room_extraction_voronoi(image):
    """
    Extract room names from floor plan snippet for Voronoi analysis.
    
    Identifies and extracts all visible room labels from a floor plan image,
    preserving exact naming for use in Voronoi tessellation neighbor detection.
    
    Args:
        image (str): Path to floor plan image
    
    Returns:
        str: JSON string containing array of room names
    
    Note:
        Used in Voronoi pipeline to supplement OCR-based room name extraction.
        Returns room names exactly as they appear (preserving spaces, capitalization).
    """
    # Encode image
    base64_image = encode_image(image)
    
    # Create message
    message = create_message_for_room_extraction_voronoi(base64_image)
    
    # Call Mistral API
    chat_response = client.chat.complete(
        model=model,
        messages=message,
        response_format={
            "type": "json_object",
        }
    )

    return chat_response.choices[0].message.content


def create_message_for_room_extraction_voronoi(base64_image):
    """
    Create Mistral API message for Voronoi room name extraction.
    
    Args:
        base64_image (str): Base64-encoded floor plan image
    
    Returns:
        list: Formatted message array for Mistral API
    """
    text = create_room_extraction_voronoi_prompt()
    
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
                    "image_url": f"data:image/png;base64,{base64_image}"
                }
            ]
        }
    ]
    return messages


# ==================== VORONOI ROOM NAMES FROM TEXT ====================

def call_mistral_roomnames(text):
    """
    Extract room names from extracted text for Voronoi neighbor detection.
    
    Filters a list of text strings to identify which ones are actual room names
    vs. measurements, annotations, or other text elements.
    
    Args:
        text (str): Concatenated text extracted from floor plan
    
    Returns:
        list: Python list of identified room names (NOT JSON string)
    
    Example:
        >>> text = "KÜCHE WC 2.50 m WOHNZIMMER 1:100 BAD"
        >>> rooms = call_mistral_roomnames(text)
        >>> print(rooms)
        ['KÜCHE', 'WC', 'WOHNZIMMER', 'BAD']
    
    Note:
        IMPORTANT: Preserves room names exactly as they appear, including:
        - Multi-word names split across text elements
        - Special characters and slashes (e.g., "WOHN/", "ESSZIMMER")
        - Spaces and capitalization
    """
    # Create message with text
    message = create_message_roomnames(text)
    
    # Call Mistral API
    chat_response = client.chat.complete(
        model=model,
        messages=message,
        response_format={
            "type": "json_object",
        }
    )
    
    # Parse JSON response to Python dict
    response_json = json.loads(chat_response.choices[0].message.content)
    
    # Extract the room names array
    room_names = response_json.get("room_names", [])
    
    return room_names  # Returns Python list directly


def create_message_roomnames(text):
    """
    Create Mistral API message for room name extraction from text.
    
    Args:
        text (str): Text content from floor plan
    
    Returns:
        list: Formatted message array for Mistral API
    """
    prompt = create_room_name_extraction_prompt(text)
      
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]
    return messages


# ==================== VORONOI CONNECTED ROOMS (VISION) ====================

def call_mistral_connected_rooms(base64_image, text):
    """
    Determine which neighboring rooms have actual doorway connections.
    
    Uses Mistral vision to analyze floor plan image and identify which rooms
    (from Voronoi neighbor candidates) are actually connected by doors/openings.
    
    Args:
        base64_image (str): Base64-encoded floor plan image
        text (str): JSON string of neighboring rooms from Voronoi analysis
    
    Returns:
        str: JSON string containing:
             {
                 "ROOM_NAME": ["CONNECTED_ROOM1", "CONNECTED_ROOM2"],
                 ...
             }
             Plus confidence score
    
    Example:
        >>> neighbors = '{"KÜCHE": ["WOHNZIMMER", "FLUR"], ...}'
        >>> base64_img = encode_image('floorplan.png')
        >>> connected = call_mistral_connected_rooms(base64_img, neighbors)
        >>> data = json.loads(connected)
        >>> # data shows only rooms with actual doors between them
    
    Note:
        This refines Voronoi geometric neighbors to actual functional connections.
        Voronoi may show rooms as neighbors if they share a wall, but this function
        identifies only those with doorways/openings.
    """
    max_retries = 3 # To avoid to many attempts at the 
    retry_delay = 60 # Start with 5 seconds
    message = create_message_connected(base64_image, text)
    for attempt in range(max_retries):
        try:
             # Call Mistral Vision API
            chat_response = client.chat.complete(
                model=model,
                messages=message,
                response_format={
                    "type": "json_object",
                }
            )
    
            return chat_response.choices[0].message.content  
            
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                print(f"⏳ Rate limited. Waiting {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Double the delay each time
            else:
                raise  # Re-raise if not rate limit or max retries reached
    # Create message with image and neighbor data
    
    
   


def create_message_connected(base64_image, text):
    """
    Create Mistral API message structure for connected rooms extraction.
    
    Combines system prompt (role definition) with user prompt (task + image).
    
    Args:
        base64_image (str): Base64-encoded floor plan image
        text (str): JSON string with neighboring rooms information from Voronoi
    
    Returns:
        list: Messages array for Mistral API with system and user roles
    """
    # Get prompts from prompt creation function
    system_prompt, user_prompt = create_connected_rooms_extraction_prompt(text)
      
    # Build two-part message: system role + user task with image
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                }
            ]
        }
    ]
    
    return messages


# ==================== FILE ENCODING UTILITIES ====================

def encode_image(image_path):
    """
    Encode an image file to base64 string for API transmission.
    
    Args:
        image_path (str): Path to image file (JPG, PNG, etc.)
    
    Returns:
        str: Base64-encoded string of image data, or None if error
    
    Example:
        >>> base64_str = encode_image('floorplan.png')
        >>> # Can now send to vision API
    """
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
    """
    Encode a PDF file to base64 string for API transmission.
    
    Args:
        pdf_path (str): Path to PDF file
    
    Returns:
        str: Base64-encoded string of PDF data, or None if error
    """
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
    """
    Determine file type based on file extension.
    
    Args:
        file_path (str): Path to file
    
    Returns:
        str: 'pdf', 'image', or 'unknown'
    
    Supported formats:
        - PDF: .pdf
        - Images: .jpg, .jpeg, .png, .gif, .bmp, .webp
    """
    extension = file_path.lower().split('.')[-1]
    
    if extension in ['pdf']:
        return 'pdf'
    elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        return 'image'
    else:
        return 'unknown'


def encode_file(file_path):
    """
    Encode either an image or PDF to base64 with automatic type detection.
    
    Automatically detects file type and applies appropriate encoding,
    returning both the base64 data and metadata needed for API calls.
    
    Args:
        file_path (str): Path to file (image or PDF)
    
    Returns:
        tuple: (base64_data, file_type, media_type)
            - base64_data (str): Base64-encoded file content
            - file_type (str): 'pdf' or 'image'
            - media_type (str): MIME type for API ('application/pdf' or 'image/jpeg')
    
    Raises:
        ValueError: If file type is unsupported or encoding fails
    
    Example:
        >>> data, ftype, mime = encode_file('plan.pdf')
        >>> print(f"Type: {ftype}, MIME: {mime}")
        Type: pdf, MIME: application/pdf
    """
    # Detect file type
    file_type = get_file_type(file_path)
    
    # Encode based on type
    if file_type == 'pdf':
        base64_data = encode_pdf(file_path)
        media_type = "application/pdf"
    elif file_type == 'image':
        base64_data = encode_image(file_path)
        media_type = "image/jpeg"
    else:
        raise ValueError(
            f"Unsupported file type for {file_path}. "
            "Supported types: PDF, JPG, JPEG, PNG, GIF, BMP, WEBP"
        )
    
    # Validate encoding succeeded
    if base64_data is None:
        raise ValueError(f"Failed to encode file: {file_path}")
    
    return base64_data, file_type, media_type


# ==================== PROMPT TEMPLATES ====================
# (Prompt creation functions below - these define the AI instructions)

def create_titleblock_extraction_prompt():
    """
    Create comprehensive prompt for title block extraction from images.
    
    Returns:
        str: Detailed prompt instructing AI to extract 13 standard title block fields
             from architectural drawings in German or English.
    
    Extracted fields:
        Project Info: ID, name, location, author, client, architect, engineers, 
                     completion year, approval date
        Plan Metadata: type, format, scale, projection method
        
    Note:
        Includes extensive examples of German and English terminology for each field.
    """
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
    """
    Create prompt for title block extraction from pre-extracted text.
    
    Similar to image-based extraction but works with text that has already
    been extracted from the PDF using OCR or text extraction tools.
    
    Args:
        extracted_text (str): Text content from title block region
    
    Returns:
        str: Detailed prompt with embedded text for AI analysis
    """
    prompt = f"""
Architectural Title Block Information Extraction

You are an expert at extracting structured information from architectural drawing title blocks in both German and English.

Your Task
Analyze the extracted text below and identify key metadata fields commonly found in architectural title blocks. Extract ONLY information that is explicitly present in the text.

[... same field definitions as image-based prompt ...]

Extracted Text to Analyze
{extracted_text}

Extract the information now.
"""
    return prompt


def create_room_adjacency_extraction_prompt():
    """
    Create prompt for extracting room adjacency relationships from floor plans.
    
    Returns:
        str: Detailed prompt instructing AI to identify:
             - Neighboring rooms (share walls)
             - Connected rooms (have doorways)
             
    Note:
        Includes extensive instructions on German/English room terminology
        and rules for reciprocal relationship mapping.
    """
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


def create_room_extraction_voronoi_prompt():
    """
    Create prompt for extracting room names from floor plan for Voronoi analysis.
    
    Returns:
        str: Simple prompt focused on exact room name extraction without interpretation
        
    Note:
        Emphasizes preserving exact spelling, capitalization, and formatting
        to match with OCR-extracted text in Voronoi pipeline.
    """
    prompt = """Analyze this architectural floorplan snippet and identify all room names that are visible in the image.

Instructions:
- Extract ONLY the room names that are explicitly labeled in the floorplan
- Copy each room name EXACTLY as it appears in the image, preserving:
  - Exact spelling and capitalization
  - Spaces, hyphens, and punctuation
  - Abbreviations (e.g., "WC" not "Water Closet")
- If a room type appears multiple times with the same label, include them as often as present in the list
- Do not infer or add room names that are not explicitly labeled
- Return the result as a valid JSON array of strings

Output format:
["Room Name 1", "Room Name 2", "Room Name 3"]

Example output:
["Bedroom", "WC", "Living Room", "Kitchen"]"""
    return prompt


def create_room_name_extraction_prompt(text_content):
    """
    Create prompt for filtering room names from extracted text (German-focused).
    
    Args:
        text_content (str): All text extracted from floor plan
    
    Returns:
        str: Prompt instructing AI to identify which text elements are room names
        
    Critical instruction:
        DO NOT combine split room names - preserve them exactly as extracted.
        E.g., "WOHN/" and "ESSZIMMER" should stay separate, not become "Wohnzimmer"
    """
    prompt = f"""Du bist ein Experte für deutsche Architekturpläne und Grundrisse. Deine Aufgabe ist es, aus einer Liste von Textelementen nur die Raumbezeichnungen zu identifizieren und zurückzugeben.

**Eingabe:**
Eine Liste von Textstrings, die aus einem Grundriss extrahiert wurden.

**Aufgabe:**
Extrahiere NUR die Texte, die Raumbezeichnungen sind. Gib sie als Python-Liste von Strings zurück.

Wichtig !!!! 
bitte kombiniere die Raumnamen nicht selbst sondern gib sie so zurück wie sie im extrahierten Text vorkommen.
also z.b "WOHN/", "ESSZIMMER" und nicht "Wohnzimmer" und "Esszimmer"
oder "grünes" , "Zimmer" und nicht "Grünes Zimmer"
oder 'ABSTELL',  'ZIMMER' und nicht als 'Abstell zimmer' 

**Was sind Raumbezeichnungen?**
- Räume wie: Wohnzimmer, Schlafzimmer, Küche, Bad, WC, Flur, Diele, Abstellraum
- Funktionsbereiche wie: Eingang, Balkon, Terrasse, Garage, Keller
- Abkürzungen wie: SZ, WZ, AR, HWR, TFL
- Mit Nummern versehene Räume wie: Zimmer 1, Raum 2.1, Büro 3

**Was sind KEINE Raumbezeichnungen?**
- Maßangaben (z.B. "2.50", "120 cm")
- Höhenangaben (z.B. "h=2.40")
- Flächenangaben (z.B. "15 m²", "qm")
- Achsbezeichnungen (z.B. "A", "B", "1", "2")
- Maßstabsangaben (z.B. "1:100")
- Bauspezifische Begriffe (z.B. "Wand", "Tür", "Fenster")
- Bereiche wie Brandabschnitt (z.B Brandabschnitt Wohnung 1)
- Plankopf-Informationen (Projektnamen, Adressen, Plannummern)
- Allgemeine Beschriftungen (z.B. "Grundriss", "Schnitt A-A")
- Einzelne Buchstaben oder Zahlen ohne Kontext
- Technische Angaben (z.B. "DN 100", "Ø 50")

**Textdatei-Inhalt:**
{text_content}

**Antwortformat:**
{{
    "room_names": ["Wohnzimmer", "Küche", "Bad", ...]
}}
"""
    return prompt


def create_connected_rooms_extraction_prompt(text_content):
    """
    Create prompt for determining actual doorway connections between rooms.
    
    Takes Voronoi neighbor candidates and floor plan image to identify which
    neighboring rooms actually have doors/openings between them.
    
    Args:
        text_content (str): JSON string of neighboring rooms from Voronoi analysis
    
    Returns:
        tuple: (system_prompt, user_prompt)
            - system_prompt: Defines AI's role as floor plan analyst
            - user_prompt: Task instructions with neighbor data
            
    Note:
        This is used in the Voronoi pipeline to refine geometric neighbors
        to actual functional connections based on visual door detection.
    """
    system_prompt = """Du bist ein Experte für die Analyse von Architekturplänen und Grundrissen. 
Deine Aufgabe ist es, aus einem Grundriss-Bild und einer Liste von benachbarten Räumen zu bestimmen, 
welche Räume tatsächlich durch Türen, Durchgänge oder Öffnungen miteinander verbunden sind."""

    user_prompt = f"""Analysiere den bereitgestellten Grundriss und die folgende Information über benachbarte Räume:

{text_content}

AUFGABE:
Bestimme auf Basis des Grundriss-Bildes, welche Räume tatsächlich durch Türen, Durchgänge oder Öffnungen physisch miteinander verbunden sind.

WICHTIGE REGELN:
1. Nur Räume, die eine direkte Verbindung (Tür, Durchgang, offene Verbindung) haben, sollen als "connected" markiert werden
2. Räume, die nur durch eine Wand getrennt sind (ohne Tür/Durchgang), sind NICHT verbunden
3. Achte auf Türsymbole, Durchgangsmarkierungen und offene Bereiche im Grundriss
4. Berücksichtige die räumliche Anordnung und die angegebenen benachbarten Räume

AUSGABEFORMAT:
Gib das Ergebnis als einzelnes JSON-Objekt zurück mit folgender Struktur:

{{
  "ROOM_NAME_1": ["CONNECTED_ROOM_1", "CONNECTED_ROOM_2"],
  "ROOM_NAME_2": ["CONNECTED_ROOM_1"],
  "confidence": 0.95
}}

Beispiel:
{{
  "ABSTELL ZIMMER": ["DIELE"],
  "BAD": ["DIELE"],
  "DIELE": ["ABSTELL ZIMMER", "BAD", "GÄSTEZIMMER", "HWR", "KÜCHE", "WOHN/ESSZIMMER"],
  "GÄSTEZIMMER": ["DIELE"],
  "HWR": ["DIELE"],
  "KÜCHE": ["DIELE", "WOHN/ESSZIMMER"],
  "TERRASSE": ["KÜCHE", "WOHN/ESSZIMMER"],
  "WOHN/ESSZIMMER": ["DIELE", "KÜCHE"],
  "confidence": 0.9
}}

Analysiere nun den Grundriss und gib NUR das JSON-Objekt zurück, ohne zusätzlichen Text oder Markdown-Formatierung."""
    
    return system_prompt, user_prompt