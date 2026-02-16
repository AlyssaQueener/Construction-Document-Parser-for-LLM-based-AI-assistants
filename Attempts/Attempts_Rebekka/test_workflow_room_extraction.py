

import sys
import cv2 as cv
import numpy as np
import pytesseract


def extract_text_from_floorplan(image, lang='deu', confidence_threshold=70):
    """
    Extract text annotations from a floor plan image using OCR.
    
    Uses Tesseract OCR to detect and extract text elements (labels, annotations,
    room names) from the floor plan, returning their content and bounding boxes.
    
    Args:
        image (np.ndarray): Grayscale input image (floor plan)
        lang (str): Tesseract language code ('deu' for German, 'eng' for English)
        confidence_threshold (int): Minimum OCR confidence score (0-100) to accept text
    
    Returns:
        list[dict]: List of detected text elements, each containing:
                    - 'text': The detected text string
                    - 'confidence': OCR confidence score
                    - 'bbox': Dictionary with x, y, width, height coordinates
    
    Note:
        Only extracts word-level text (level 5) to filter out noise.
    """
    extracted_text_data = []
    
    # Perform OCR to get bounding box data
    # PSM 11: Sparse text with no particular orientation
    data = pytesseract.image_to_data(
        image, 
        output_type=pytesseract.Output.DICT, 
        lang=lang, 
        config='--psm 11'
    )
    
    n_boxes = len(data['level'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        
        # Filter: non-empty text, sufficient confidence, word-level only (level 5)
        if text and conf > confidence_threshold and data['level'][i] == 5:
            x = data['left'][i]
            y = data['top'][i]
            w_text = data['width'][i]
            h_text = data['height'][i]
            
            extracted_text_data.append({
                'text': text,
                'confidence': conf,
                'bbox': {'x': x, 'y': y, 'width': w_text, 'height': h_text}
            })
    
    return extracted_text_data


def remove_text_from_image(image, text_data):
    """
    Remove detected text from an image by drawing white rectangles over text regions.
    
    Creates a clean copy of the floor plan with text annotations removed,
    preparing it for wall and room detection algorithms.
    
    Args:
        image (np.ndarray): Original grayscale image
        text_data (list[dict]): Text bounding boxes from extract_text_from_floorplan()
    
    Returns:
        np.ndarray: Copy of image with text regions filled with white (255)
    """
    img_cleaned = image.copy()
    
    # Draw white rectangles over detected text areas
    for item in text_data:
        bbox = item['bbox']
        x, y, w_text, h_text = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        # Fill with white (255) to remove text
        cv.rectangle(img_cleaned, (x, y), (x + w_text, y + h_text), (255), -1)
    
    return img_cleaned


def preprocess_floorplan(image):
    """
    Preprocess floor plan image for wall detection.
    
    Applies noise reduction and adaptive thresholding to create a binary image
    where walls/lines are white and background is black.
    
    Args:
        image (np.ndarray): Grayscale input image
    
    Returns:
        np.ndarray: Binary image (walls=white, background=black)
    
    Processing steps:
        1. Gaussian blur (5x5) to reduce noise
        2. Adaptive threshold with mean method (21x21 neighborhood)
        3. Binary inversion (walls become white)
    """
    # Apply Gaussian Blur to reduce noise
    blurred = cv.GaussianBlur(image, (5, 5), 0)
    
    # Adaptive threshold: converts to binary based on local neighborhood
    # THRESH_BINARY_INV: walls/lines become white (255), background black (0)
    binary = cv.adaptiveThreshold(
        blurred, 
        255, 
        cv.ADAPTIVE_THRESH_MEAN_C,  # Compute mean of neighboring pixels
        cv.THRESH_BINARY_INV, 
        21,  # Size of neighborhood
        3    # Constant subtracted from mean
    )
    
    return binary


def filter_walls_from_furniture(binary_image, image_dimensions):
    """
    Separate wall components from furniture and fixtures using morphological analysis.
    
    Analyzes connected components to distinguish between structural walls
    (long, thin, large area) and furniture/fixtures (compact, moderate aspect ratio).
    
    Args:
        binary_image (np.ndarray): Binary image from preprocessing
        image_dimensions (tuple): (height, width) of the image
    
    Returns:
        np.ndarray: Filtered binary image containing only wall-like components
    
    Classification criteria:
        Walls: Large area (>500px), extreme aspect ratio (>3.0 or <0.33), or >0.5% of image
        Furniture: Moderate area (10-8000px), balanced aspect ratio (0.5-2.0)
    """
    h, w = image_dimensions
    
    # Find all connected components
    num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(
        binary_image, 
        connectivity=8
    )
    
    # Create blank image for filtered results
    filtered_binary = np.zeros_like(binary_image)
    
    # Define thresholds for wall vs furniture classification
    min_wall_area_keep = 500  # Minimum area for walls
    max_wall_area_keep = (h * w) * 0.8  # Maximum area (exclude full-image borders)
    min_wall_aspect_ratio_thin_line = 3.0  # For horizontal walls
    max_wall_aspect_ratio_thin_line = 0.33  # For vertical walls
    
    min_furniture_area_discard = 10
    max_furniture_area_discard = 8000
    min_furniture_aspect_discard = 0.5
    max_furniture_aspect_discard = 2.0
    
    # Iterate through each component (label 0 is background)
    for i in range(1, num_labels):
        area = stats[i, cv.CC_STAT_AREA]
        width = stats[i, cv.CC_STAT_WIDTH]
        height = stats[i, cv.CC_STAT_HEIGHT]
        aspect_ratio = float(width) / height if height != 0 else 9999
        
        # Step 1: Check if component matches wall-like criteria
        is_wall_component = False
        
        if (area > min_wall_area_keep and area < max_wall_area_keep):
            # Long thin lines (walls)
            if (aspect_ratio > min_wall_aspect_ratio_thin_line or 
                aspect_ratio < max_wall_aspect_ratio_thin_line):
                is_wall_component = True
            # Or large structural components
            elif area > (h * w) * 0.005:  # >0.5% of total image area
                is_wall_component = True
        
        # Step 2: Exclude furniture-like components
        if (area > min_furniture_area_discard and area < max_furniture_area_discard) and \
           (aspect_ratio >= min_furniture_aspect_discard and aspect_ratio <= max_furniture_aspect_discard):
            is_wall_component = False
        
        # Step 3: Add to filtered image if it's a wall
        if is_wall_component:
            filtered_binary[labels == i] = 255
    
    return filtered_binary


def detect_wall_edges(filtered_image):
    """
    Detect and enhance wall edges using morphological operations.
    
    Applies morphological operations to connect broken wall segments and
    fill small gaps, creating continuous wall boundaries.
    
    Args:
        filtered_image (np.ndarray): Binary image with wall components only
    
    Returns:
        np.ndarray: Enhanced binary image with connected wall boundaries
    
    Processing steps:
        1. Morphological opening (3x3) to remove small noise
        2. Canny edge detection (thresholds: 50, 150)
        3. Dilation (3x3, 3 iterations) to thicken edges
        4. Morphological closing (31x31) to connect wall segments
    """
    # Small morphological opening to clean up noise
    kernel_cleanup_small = np.ones((3, 3), np.uint8)
    cleaned = cv.morphologyEx(filtered_image, cv.MORPH_OPEN, kernel_cleanup_small)
    
    # Canny edge detection
    edges = cv.Canny(cleaned, 50, 150)
    
    # Dilate edges to thicken walls
    kernel = np.ones((3, 3), np.uint8)
    edges_dilated = cv.dilate(edges, kernel, iterations=3)
    
    # Strong closing to connect broken wall segments
    kernel_big = np.ones((31, 31), np.uint8)
    walls = cv.morphologyEx(edges_dilated, cv.MORPH_CLOSE, kernel_big)
    
    return walls


def extract_region_of_interest(image, roi_percentages=(0.15, 0.25, 0.85, 0.75)):
    """
    Extract the central region of interest from a floor plan, removing borders.
    
    Creates a mask to isolate the main floor plan area, excluding title blocks,
    legends, and border annotations.
    
    Args:
        image (np.ndarray): Input binary image
        roi_percentages (tuple): (x_min, y_min, x_max, y_max) as fractions of image size
                                Default: (0.15, 0.25, 0.85, 0.75) = central 70%x50% area
    
    Returns:
        np.ndarray: Masked image showing only the ROI
    
    Note:
        Adjust roi_percentages based on your floor plan layout.
        Default values exclude 15% from each side and 25% from top/bottom.
    """
    h, w = image.shape
    
    # Calculate ROI coordinates
    x_min_roi = int(w * roi_percentages[0])
    y_min_roi = int(h * roi_percentages[1])
    x_max_roi = int(w * roi_percentages[2])
    y_max_roi = int(h * roi_percentages[3])
    
    # Create black mask
    mask = np.zeros_like(image)
    
    # Draw white rectangle in ROI
    cv.rectangle(mask, (x_min_roi, y_min_roi), (x_max_roi, y_max_roi), 255, -1)
    
    # Apply mask
    roi_image = cv.bitwise_and(image, mask)
    
    return roi_image


def detect_wall_contours(walls_image):
    """
    Detect contours of walls in the processed floor plan.
    
    Finds boundaries of connected wall components for visualization
    or further geometric analysis.
    
    Args:
        walls_image (np.ndarray): Binary image with detected walls
    
    Returns:
        tuple: (contours, hierarchy) from cv.findContours
               - contours: List of detected contours
               - hierarchy: Hierarchical relationship between contours
    
    Note:
        Uses RETR_TREE to capture full hierarchy of nested contours.
    """
    contours, hierarchy = cv.findContours(
        walls_image, 
        cv.RETR_TREE, 
        cv.CHAIN_APPROX_SIMPLE
    )
    
    return contours, hierarchy


def draw_wall_contours(contours, image_dimensions):
    """
    Visualize detected wall contours on a white canvas.
    
    Args:
        contours (list): Wall contours from detect_wall_contours()
        image_dimensions (tuple): (height, width) for output image
    
    Returns:
        np.ndarray: RGB image with walls drawn in black on white background
    """
    h, w = image_dimensions
    
    # Create white background
    output = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    # Draw all contours filled in black
    cv.drawContours(output, contours, -1, (0, 0, 0), thickness=cv.FILLED)
    
    return output


def process_floorplan(filename, lang='deu', show_visualization=True):
    """
    Complete pipeline for processing architectural floor plan images.
    
    Extracts text annotations, removes them, detects walls, and isolates
    structural elements from furniture and fixtures.
    
    Args:
        filename (str): Path to floor plan image file
        lang (str): OCR language code ('deu' for German, 'eng' for English)
        show_visualization (bool): If True, display intermediate processing steps
    
    Returns:
        dict: Processing results containing:
              - 'text_data': Extracted text annotations
              - 'walls_roi': Binary image of walls in ROI
              - 'contours': Detected wall contours
              - 'visualization': RGB image with drawn contours
    
    Pipeline:
        1. Load image in grayscale
        2. Extract text with OCR
        3. Remove text from image
        4. Preprocess (blur + threshold)
        5. Filter walls from furniture
        6. Detect and enhance edges
        7. Extract region of interest
        8. Detect wall contours
    
    Example:
        >>> results = process_floorplan('floorplan.png', lang='eng')
        >>> print(f"Found {len(results['text_data'])} text elements")
        >>> cv.imshow("Result", results['visualization'])
    """
    # [1] Load image
    src = cv.imread(filename, cv.IMREAD_GRAYSCALE)
    if src is None:
        raise FileNotFoundError(f"Failed to load image: {filename}")
    
    h, w = src.shape
    print(f"Loaded image: {w}x{h} pixels")
    
    # [2] Extract text annotations
    print("Extracting text with OCR...")
    text_data = extract_text_from_floorplan(src, lang=lang)
    print(f"Extracted {len(text_data)} text elements")
    
    # [3] Remove text from image
    img_cleaned = remove_text_from_image(src, text_data)
    
    # [4] Preprocess image
    print("Preprocessing image...")
    binary = preprocess_floorplan(img_cleaned)
    
    # [5] Filter walls from furniture
    print("Filtering walls from furniture...")
    filtered_walls = filter_walls_from_furniture(binary, (h, w))
    
    # [6] Detect and enhance wall edges
    print("Detecting wall edges...")
    walls = detect_wall_edges(filtered_walls)
    
    # [7] Extract region of interest
    print("Extracting ROI...")
    walls_roi = extract_region_of_interest(walls)
    
    # [8] Detect wall contours
    print("Detecting contours...")
    contours, hierarchy = detect_wall_contours(walls_roi)
    print(f"Found {len(contours)} contours")
    
    # [9] Visualize results
    visualization = draw_wall_contours(contours, (h, w))
    
    # Display intermediate steps if requested
    if show_visualization:
        cv.imshow("Original Source", src)
        cv.imshow("Text Removed", img_cleaned)
        cv.imshow("Binary (Thresholded)", binary)
        cv.imshow("Filtered Walls", filtered_walls)
        cv.imshow("Enhanced Walls", walls)
        cv.imshow("Walls within ROI", walls_roi)
        cv.imshow("Detected Wall Contours (Filled)", visualization)
        cv.waitKey()
        cv.destroyAllWindows()
    
    return {
        'text_data': text_data,
        'walls_roi': walls_roi,
        'contours': contours,
        'hierarchy': hierarchy,
        'visualization': visualization
    }


# Main execution
if __name__ == "__main__":
    filename = 'examples/FloorplansAndSectionViews/Cluttered Plan/Cluttered 03_page1.png'
    
    try:
        results = process_floorplan(filename, lang='deu', show_visualization=True)
        print("\nProcessing complete!")
        print(f"Extracted text: {[item['text'] for item in results['text_data']]}")
    except Exception as e:
        print(f"Error processing floor plan: {e}")
        sys.exit(1)

