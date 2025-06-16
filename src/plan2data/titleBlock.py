import cv2
import pytesseract
import numpy as np
from matplotlib import pyplot as plt

def init_title_block_extraction(image_path):
    # Load and preprocess image
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    data = pytesseract.image_to_data(image_rgb, output_type=pytesseract.Output.DICT)
    return extract_right_side_titleblock(image_rgb, data)

def extract_right_side_titleblock(image_rgb, data):
    height, width = image_rgb.shape[:2]
    right_boundary = int(width * 0.7)
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
        titleblock_region = {
            'x': max(0, min_x - margin),
            'y': max(0, min_y - margin),
            'width': min(width - (min_x - margin), max_x - min_x + 2*margin),
            'height': min(height - (min_y - margin), max_y - min_y + 2*margin)
        }
        
        return titleblock_region
    
    return None

def visualize_results(image_rgb, titleblock_region):    
    result_image = image_rgb.copy()
    x, y, w, h = titleblock_region['x'], titleblock_region['y'], titleblock_region['width'], titleblock_region['height']
    
    # Draw rectangle around detected titleblock
    cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 0, 0), 3)
    
    # Extract the titleblock region
    titleblock_extracted = image_rgb[y:y+h, x:x+w]
    
    # Display results
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.imshow(image_rgb)
    plt.title("Original Image")
    plt.axis("off")
    
    plt.subplot(1, 3, 2)
    plt.imshow(result_image)
    plt.title(f"Detected Titleblock")
    plt.axis("off")
    
    plt.subplot(1, 3, 3)
    plt.imshow(titleblock_extracted)
    plt.title("Extracted Titleblock")
    plt.axis("off")
    
    plt.tight_layout()
    plt.show()
    
    return titleblock_extracted


def extract_text_titleblock(image_path, titleblock_region):
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    x, y, w, h = titleblock_region['x'], titleblock_region['y'], titleblock_region['width'], titleblock_region['height']
    titleblock = image_rgb[y:y+h, x:x+w]
    text_title_block = pytesseract.image_to_string(titleblock)
    return text_title_block

def save_image_of_titleblock_and_floorplan(image_path, titleblock_region, output_path_titleblock, output_path_floorplan):
    # Load image and extract region
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    x, y, w, h = titleblock_region['x'], titleblock_region['y'], titleblock_region['width'], titleblock_region['height']
    titleblock = image_rgb[y:y+h, x:x+w]
    floorplan = image_rgb[:, :x-10]  
    
    # Save if output path provided
    if output_path_floorplan and output_path_titleblock:
        titleblock_bgr = cv2.cvtColor(titleblock, cv2.COLOR_RGB2BGR)
        floorplan_bgr = cv2.cvtColor(floorplan, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path_titleblock, titleblock_bgr) # specify the file name like floorplan.png
        cv2.imwrite(output_path_floorplan, floorplan_bgr)

        print(f"Title block saved to: {output_path_titleblock}")
        print(f"Title block saved to: {output_path_floorplan}")
    
