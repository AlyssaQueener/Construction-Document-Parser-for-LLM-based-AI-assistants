import cv2
import pytesseract
import numpy as np
from matplotlib import pyplot as plt
from collections import defaultdict
import os 
from mistralai import Mistral

api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"

def extract_floorplan_stamp_density(image_path, method='right_side_detection'):
    """
    Extract floor plan stamp using different methods optimized for right-side title blocks
    
    Args:
        image_path: Path to the floor plan image
        method: 'right_side_detection', 'density_grid', 'clustering', or 'contour_analysis'
    """
    
    # Load and preprocess image
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Extract text data
    data = pytesseract.image_to_data(image_rgb, output_type=pytesseract.Output.DICT)
    
    if method == 'right_side_detection':
        return extract_right_side_titleblock(image_rgb, data)


def extract_right_side_titleblock(image_rgb, data):
    """
    Specialized method for extracting right-side architectural title blocks
    """
    height, width = image_rgb.shape[:2]
    
    # Focus on the right portion of the image (typically where title blocks are located)
    right_boundary = int(width * 0.7)  # Look in rightmost 40% of image
    
    # Collect text boxes in the right region
    right_text_boxes = []
    n_boxes = len(data['level'])
    
    for i in range(n_boxes):
        if int(data['conf'][i]) > 30:  # Filter low confidence
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            # Only consider text boxes in the right portion
            if x > right_boundary and w > 0 and h > 0:
                right_text_boxes.append({
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'area': w * h,
                    'text': data['text'][i].strip()
                })
    
    if not right_text_boxes:
        return None, None
    
    # Find the bounding box that encompasses most text in the right region
    if right_text_boxes:
        # Get overall bounds of all text boxes in right region
        min_x = min(box['x'] for box in right_text_boxes)
        max_x = max(box['x'] + box['w'] for box in right_text_boxes)
        min_y = min(box['y'] for box in right_text_boxes)
        max_y = max(box['y'] + box['h'] for box in right_text_boxes)
        
        # Add some margin
        margin = 10
        stamp_region = {
            'x': max(0, min_x - margin),
            'y': max(0, min_y - margin),
            'width': min(width - (min_x - margin), max_x - min_x + 2*margin),
            'height': min(height - (min_y - margin), max_y - min_y + 2*margin)
        }
        
        return stamp_region, right_text_boxes
    
    return None, None





def visualize_results(image_rgb, stamp_region, method_name):
    """Visualize the extracted stamp region"""
    
    if stamp_region is None:
        print(f"No stamp region found using {method_name}")
        return
    
    # Create visualization
    result_image = image_rgb.copy()
    x, y, w, h = stamp_region['x'], stamp_region['y'], stamp_region['width'], stamp_region['height']
    
    # Draw rectangle around detected stamp
    cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 0, 0), 3)
    
    # Extract the stamp region
    stamp_extracted = image_rgb[y:y+h, x:x+w]
    
    # Display results
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.imshow(image_rgb)
    plt.title("Original Image")
    plt.axis("off")
    
    plt.subplot(1, 3, 2)
    plt.imshow(result_image)
    plt.title(f"Detected Stamp ({method_name})")
    plt.axis("off")
    
    plt.subplot(1, 3, 3)
    plt.imshow(stamp_extracted)
    plt.title("Extracted Stamp")
    plt.axis("off")
    
    plt.tight_layout()
    plt.show()
    
    return stamp_extracted

# Example usage optimized for your floor plan

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

def main():
    image_path = "bemasster-grundriss-plankopf_page1.png"
    output_path = "examples.png"
    
    print("Extracting right-side architectural title block...")
    
    # Method 1: Right-side detection (best for your layout)
    print("\n1. Right-side Title Block Detection:")
    stamp_region, right_text_boxes = extract_floorplan_stamp_density(image_path, 'right_side_detection')
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    if stamp_region:
        stamp_extracted = visualize_results(image_rgb, stamp_region, "Right-side Detection")
        
        # Print detected text information
        if right_text_boxes:
            print(f"Found {len(right_text_boxes)} text elements in title block")
            print("Sample text detected:")
            for i, box in enumerate(right_text_boxes[:10]):  # Show first 10
                if box['text']:
                    print(f"  - {box['text']}")
    floorplan = extract_and_save_titleblock(image_path, output_path )
    floorplan_text = pytesseract.image_to_string(floorplan)
    print(floorplan_text)

    promt = create_extraction_prompt_with_examples(floorplan_text)
    print("Type Promt2")
    print(type(promt))
    model = "mistral-small-latest"

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
    print("Chat Response")
    print(chat_response.choices[0].message.content)
    
    

def extract_and_save_titleblock(image_path, output_path=None):
    """
    Simple function to extract and optionally save the title block
    """
    # Extract using the right-side method
    stamp_region, _ = extract_floorplan_stamp_density(image_path, 'right_side_detection')
    
    if stamp_region is None:
        print("Could not detect title block")
        return None
    
    # Load image and extract region
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    x, y, w, h = stamp_region['x'], stamp_region['y'], stamp_region['width'], stamp_region['height']
    titleblock = image_rgb[y:y+h, x:x+w]
    height, width = image_rgb.shape[:2]
    floorplan = image_rgb[:, :x-10]  
    
    # Save if output path provided
    if output_path:
        titleblock_bgr = cv2.cvtColor(titleblock, cv2.COLOR_RGB2BGR)
        floorplan_bgr = cv2.cvtColor(floorplan, cv2.COLOR_RGB2BGR)
        cv2.imwrite("stemp.png", titleblock_bgr)
        cv2.imwrite("floorplan1.png", floorplan_bgr)

        print(f"Title block saved to: {output_path}")
    
    return titleblock

if __name__ == "__main__":
    main()