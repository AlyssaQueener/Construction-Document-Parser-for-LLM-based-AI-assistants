import cv2
import easyocr
import numpy as np
from matplotlib import pyplot as plt

# Initialize EasyOCR reader (you can specify languages as needed)
reader = easyocr.Reader(['en','de'])  # Add more languages like ['en', 'de', 'fr'] if needed

## inits-> loading and preprocessing image (with ai-> localization is added)
def init_title_block_extraction(image_path):
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)    
    data = easyocr_image_to_data(image_rgb)
    return extract_right_side_titleblock(image_rgb, data)

def init_title_block_extraction_with_ai_localization(image_path, horizontal_boundry_percentage, greater_then_horizontal, vertical_boundry_percentage, greater_then_vertical):
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)    
    data = easyocr_image_to_data(image_rgb)
    return extract_titleblock_with_ai_localization(image_rgb, data, horizontal_boundry_percentage, greater_then_horizontal, vertical_boundry_percentage, greater_then_vertical)

def easyocr_image_to_data(image):
    """
    Convert EasyOCR results to pytesseract-like data format
    """
    results = reader.readtext(image)
    
    data = {
        'level': [],
        'page_num': [],
        'block_num': [],
        'par_num': [],
        'line_num': [],
        'word_num': [],
        'left': [],
        'top': [],
        'width': [],
        'height': [],
        'conf': [],
        'text': []
    }
    
    for i, (bbox, text, confidence) in enumerate(results):
        # Extract bounding box coordinates
        # bbox is in format [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        
        left = int(min(x_coords))
        top = int(min(y_coords))
        width = int(max(x_coords) - min(x_coords))
        height = int(max(y_coords) - min(y_coords))
        
        # Convert confidence to percentage (EasyOCR gives 0-1, pytesseract uses 0-100)
        conf = int(confidence * 100)
        
        # Populate data dictionary
        data['level'].append(5)  # Word level (similar to pytesseract)
        data['page_num'].append(1)
        data['block_num'].append(1)
        data['par_num'].append(1)
        data['line_num'].append(i + 1)
        data['word_num'].append(i + 1)
        data['left'].append(left)
        data['top'].append(top)
        data['width'].append(width)
        data['height'].append(height)
        data['conf'].append(conf)
        data['text'].append(text)
    
    return data

## extracts titleblock under the assumption that it is localized in the right third of image
def extract_right_side_titleblock(image_rgb, data):
    height, width = image_rgb.shape[:2]
    right_boundary = int(width * 0.7)
    titleblock_text_boxes = []
    n_boxes = len(data['level'])
    
    for i in range(n_boxes):
        if int(data['conf'][i]) > 30:  
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            if x > right_boundary and w > 0 and h > 0:
                titleblock_text_boxes.append({
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'area': w * h,
                    'text': data['text'][i].strip()
                })
    
    if not titleblock_text_boxes:
        return None
    
    
    if titleblock_text_boxes:
        min_x = min(box['x'] for box in titleblock_text_boxes)
        max_x = max(box['x'] + box['w'] for box in titleblock_text_boxes)
        min_y = min(box['y'] for box in titleblock_text_boxes)
        max_y = max(box['y'] + box['h'] for box in titleblock_text_boxes)
        
        margin = 10
        titleblock_region = {
            'x': max(0, min_x - margin),
            'y': max(0, min_y - margin),
            'width': min(width - (min_x - margin), max_x - min_x + 2*margin),
            'height': min(height - (min_y - margin), max_y - min_y + 2*margin)
        }
        
        return titleblock_region
    
    return None

def extract_titleblock_with_ai_localization(image_rgb, data, horizontal_boundary_percentage, greater_then_horizontal, vertical_boundary_percentage, greater_then_vertical):
    height, width = image_rgb.shape[:2]
    horizontal_boundary = int(width * horizontal_boundary_percentage)
    vertical_boundary = int(height * vertical_boundary_percentage)
    
    titleblock_text_boxes = []
    n_boxes = len(data['level'])
    
    for i in range(n_boxes):
        if int(data['conf'][i]) > 30:  
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            
            in_titleblock_region = False
            
            if greater_then_vertical and greater_then_horizontal:
                in_titleblock_region = (x >= horizontal_boundary and y >= vertical_boundary)
            elif greater_then_vertical and not greater_then_horizontal:
                in_titleblock_region = (x <= horizontal_boundary and y >= vertical_boundary)
            elif not greater_then_vertical and not greater_then_horizontal:
                in_titleblock_region = (x <= horizontal_boundary and y <= vertical_boundary)
            else:  
                in_titleblock_region = (x >= horizontal_boundary and y <= vertical_boundary)
            
            if in_titleblock_region and w > 0 and h > 0:
                titleblock_text_boxes.append({
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'area': w * h,
                    'text': data['text'][i].strip()
                })
    
    if not titleblock_text_boxes:
        return None
    
    min_x = min(box['x'] for box in titleblock_text_boxes)
    max_x = max(box['x'] + box['w'] for box in titleblock_text_boxes)
    min_y = min(box['y'] for box in titleblock_text_boxes)
    max_y = max(box['y'] + box['h'] for box in titleblock_text_boxes)
    
    
    margin = 10
    titleblock_region = {
        'x': max(0, min_x+margin),
        'y': max(0, min_y+margin),
        'width': min(width - (min_x - margin), max_x - min_x + 2*margin),
        'height': min(height - (min_y - margin), max_y - min_y + 2*margin)
    }
    
    return titleblock_region

def visualize_results(image_path, titleblock_region): 
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)   
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

def visualize_extracted_titleblock(image_path,titleblock_region):
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result_image = image_rgb.copy()
    x, y, w, h = titleblock_region['x'], titleblock_region['y'], titleblock_region['width'], titleblock_region['height']
    # Extract the titleblock region
    titleblock_extracted = image_rgb[y:y+h, x:x+w]
    plt.imshow(titleblock_extracted)
    plt.title("Extracted Titleblock")
    plt.show()

def extract_text_titleblock(image_path, titleblock_region):
    if titleblock_region == None:
        return " "
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    x, y, w, h = titleblock_region['x'], titleblock_region['y'], titleblock_region['width'], titleblock_region['height']
    titleblock = image_rgb[y:y+h, x:x+w]
    
    # Use EasyOCR to extract text
    results = reader.readtext(titleblock)
    text_title_block = ""
    
    # Sort results by y-coordinate (top to bottom) then x-coordinate (left to right)
    results.sort(key=lambda x: (x[0][0][1], x[0][0][0]))
    
    for (bbox, text, confidence) in results:
        if confidence > 0.3:  # Filter by confidence (equivalent to conf > 30 in pytesseract)
            text_title_block += text + " "
    
    text_title_block = text_title_block.strip()
    print(text_title_block)
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