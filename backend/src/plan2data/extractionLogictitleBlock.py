## inits-> loading and preprocessing image 
def extract_text_titleblock(image_path):
    import cv2
    import pytesseract
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)    
    data = pytesseract.image_to_data(image_rgb, output_type=pytesseract.Output.DICT)
    titleblock_region = extract_right_side_titleblock(image_rgb, data)
    x, y, w, h = titleblock_region['x'], titleblock_region['y'], titleblock_region['width'], titleblock_region['height']
    titleblock = image_rgb[y:y+h, x:x+w]
    text_title_block = pytesseract.image_to_string(titleblock)
    print(text_title_block)
    return text_title_block


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
    



    
