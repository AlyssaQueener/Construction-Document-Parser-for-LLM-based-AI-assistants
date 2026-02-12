import json
import src.plan2data.mistralConnection as mistral 



### Workflow to identify title block in floorplan and extract key features
### Key features are displayed in terminal output


def get_neighbouring_rooms_with_ai(path):
    """
    Extract room adjacency relationships from floor plan using AI vision analysis.
    
    Sends floor plan image to Mistral AI vision model to identify neighboring rooms
    and validates the extraction quality based on confidence score.
    
    Args:
        path (str): Path to floor plan image file (PNG, JPG, PDF)
    
    Returns:
        tuple: (output, method, is_successful, confidence)
            - output (dict): Parsed JSON containing room adjacency data
            - method (str): Always "ai" for this function
            - is_successful (bool): True if confidence > 0.5
            - confidence (float): AI confidence score (0.0 to 1.0)
    
    Example:
        >>> output, method, success, conf = get_neighbouring_rooms_with_ai('floorplan.pdf')
        >>> if success:
        >>>     print(f"Rooms: {output}")
        >>>     print(f"Confidence: {conf}")
    
    Note:
        Confidence threshold of 0.5 determines success. Adjust based on your
        quality requirements.
    """
    is_successful = False
    method = "ai"
    
    # Extract room adjacency data from image using AI
    output = json.loads(extract_neighbouring_rooms_with_ai(path))
    
    # Validate extraction quality based on confidence score
    if output["confidence"] > 0.5:
        is_successful = True
    
    confidence = output["confidence"]
    
    return output, method, is_successful, confidence


def get_full_floorplan_metadata_with_ai(path):
    """
    Extract complete floor plan metadata including title block and room adjacency.
    
    Performs comprehensive AI-based extraction of all floor plan information:
    - Title block data (project info, scale, date, etc.)
    - Room adjacency relationships
    - Confidence scores for each component
    
    Args:
        path (str): Path to floor plan image file (PNG, JPG, PDF)
    
    Returns:
        tuple: (output, method, is_successful, confidence)
            - output (dict): Parsed JSON with nested structure:
                  {
                      "titleBlock": {..., "confidence": float},
                      "roomAdjacency": {..., "confidence": float}
                  }
            - method (str): Always "ai" for this function
            - is_successful (bool): True if average confidence > 0.5
            - confidence (float): Average of titleblock and room confidence scores
    
    Confidence Calculation:
        Uses average of both confidence scores. Alternative approaches:
        - Minimum: confidence = min(titleblock_confidence, room_confidence)
        - Weighted: confidence = 0.7*titleblock + 0.3*room
    
    Example:
        >>> output, method, success, conf = get_full_floorplan_metadata_with_ai('plan.pdf')
        >>> if success:
        >>>     print(f"Project: {output['titleBlock']['projectName']}")
        >>>     print(f"Rooms: {output['roomAdjacency']['rooms']}")
        >>>     print(f"Overall confidence: {conf:.2f}")
    
    Note:
        Requires both titleblock AND room extraction to succeed for is_successful=True.
        If only one component is needed, use specialized functions instead.
    """
    is_successful = False
    method = "ai"
    
    # Extract full floor plan metadata (title block + room adjacency)
    output = json.loads(extract_full_floorplan_metadata_with_ai(path))
    
    # Extract confidence scores from nested structure
    # Use .get() with default 0.0 to handle missing keys gracefully
    titleblock_confidence = output.get("titleBlock", {}).get("confidence", 0.0)
    room_confidence = output.get("roomAdjacency", {}).get("confidence", 0.0)
    
    # Calculate overall confidence as average of both components
    # Alternative approaches:
    # - Minimum (stricter): confidence = min(titleblock_confidence, room_confidence)
    # - Weighted: confidence = 0.7 * titleblock_confidence + 0.3 * room_confidence
    confidence = (titleblock_confidence + room_confidence) / 2  # Average
    
    # Validate extraction quality
    # Both components should have reasonable confidence for success
    if confidence > 0.5:
        is_successful = True
    
    return output, method, is_successful, confidence


def extract_neighbouring_rooms_with_ai(image_path):
    """
    Low-level function to call Mistral AI for room adjacency extraction.
    
    Wrapper function that interfaces with the Mistral API connection module
    to extract room adjacency relationships from floor plan images.
    
    Args:
        image_path (str): Path to floor plan image file
    
    Returns:
        str: JSON string from Mistral API containing:
             {
                 "rooms": [...],
                 "adjacency": {...},
                 "confidence": float
             }
    
    API Call:
        Uses Mistral's vision model with specialized prompt for room adjacency
        detection in architectural floor plans.
    """
    mistral_response = mistral.call_mistral_for_room_adjacency_extraction(image_path)
    return mistral_response


def extract_full_floorplan_metadata_with_ai(image_path):
    """
    Low-level function to call Mistral AI for complete floor plan extraction.
    
    Wrapper function that interfaces with the Mistral API connection module
    to extract all metadata from floor plan images including title block
    information and room relationships.
    
    Args:
        image_path (str): Path to floor plan image file
    
    Returns:
        str: JSON string from Mistral API 
    
       
    API Call:
        Uses Mistral's vision model with comprehensive prompt for extracting
        both title block metadata and spatial room relationships.
    """
    mistral_response = mistral.call_mistral_for_floorplan_extraction_from_image(image_path)
    return mistral_response