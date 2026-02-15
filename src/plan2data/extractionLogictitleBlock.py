def extract_text_titleblock(image_path: str) -> str | None:
    """
    Load a floor plan image, locate the title block region using OCR heuristics,
    crop it, and extract its text content.

    Pipeline:
        1. Read and convert the image to RGB.
        2. Run Tesseract OCR to get bounding-box data for every detected word.
        3. Use `extract_right_side_titleblock` to estimate the title block's
           bounding rectangle (assumes it sits in the right third of the image).
        4. Crop the image to that region and run a second, focused OCR pass
           to get cleaner text output.

    Args:
        image_path: File path to the floor plan image.

    Returns:
        The extracted text from the title block, or None if the image
        could not be read or OCR/CV processing failed.
    """
    import cv2
    import pytesseract

    try:
        # --- Step 1: Load image ------------------------------------------------
        image = cv2.imread(image_path)
        if image is None:
            return None

        # OpenCV loads images as BGR; convert to RGB for Tesseract
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # --- Step 2: First OCR pass — collect word-level bounding boxes ---------
        # output_type=DICT gives us parallel lists (text, conf, left, top, …)
        # that we can iterate over to find where text lives on the page.
        data = pytesseract.image_to_data(
            image_rgb,
            output_type=pytesseract.Output.DICT
        )

        # --- Step 3: Estimate title block region from detected text positions ---
        titleblock_region = extract_right_side_titleblock(image_rgb, data)

        # Unpack the bounding rectangle
        x, y, w, h = (
            titleblock_region['x'],
            titleblock_region['y'],
            titleblock_region['width'],
            titleblock_region['height'],
        )

        # --- Step 4: Crop and run a second, focused OCR pass -------------------
        # Cropping to just the title block area improves OCR accuracy by
        # removing noise from the rest of the drawing.
        titleblock = image_rgb[y:y+h, x:x+w]
        text_title_block = pytesseract.image_to_string(titleblock)

        print(text_title_block)
        return text_title_block

    except (cv2.error, pytesseract.TesseractError, KeyError, TypeError) as e:
        # KeyError / TypeError can occur if titleblock_region is None
        # (no text detected in the right third of the image)
        print("Deterministic parsing failed due to openCV or tesseract")
        print(e)
        return None


def extract_right_side_titleblock(image_rgb, data:dict)->dict:
    """
    Estimate the bounding rectangle of the title block by clustering all
    high-confidence OCR text boxes found in the right 30% of the image.

    Assumption: Architectural title blocks are conventionally placed on
    the right-hand side of the drawing sheet.

    Args:
        image_rgb:  The floor plan image as a NumPy array (H × W × 3).
        data:       Tesseract word-level detection output (dict of parallel
                    lists: 'left', 'top', 'width', 'height', 'conf', 'text', …).

    Returns:
        A dict with keys {'x', 'y', 'width', 'height'} describing the
        title block bounding box, or None if no qualifying text was found.
    """
    height, width = image_rgb.shape[:2]

    # Only consider text whose left edge starts past 70% of the image width.
    # This filters out the main drawing area and keeps title block text.
    right_boundary = int(width * 0.7)

    # Collect all text boxes that pass the position and confidence filters
    titleblock_text_boxes = []
    n_boxes = len(data['level'])

    for i in range(n_boxes):
        # Skip low-confidence detections (threshold: 30%)
        if int(data['conf'][i]) > 30:
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

            # Keep only boxes that are in the right portion and have valid dimensions
            if x > right_boundary and w > 0 and h > 0:
                titleblock_text_boxes.append({
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'area': w * h,
                    'text': data['text'][i].strip()
                })

    # No text found in the right region — title block could not be located
    if not titleblock_text_boxes:
        return None

    # ---- Compute a tight bounding box around all detected text boxes -------
    # Find the extremes of all collected boxes to form one enclosing rectangle
    min_x = min(box['x'] for box in titleblock_text_boxes)
    max_x = max(box['x'] + box['w'] for box in titleblock_text_boxes)
    min_y = min(box['y'] for box in titleblock_text_boxes)
    max_y = max(box['y'] + box['h'] for box in titleblock_text_boxes)

    # Add a small margin so the crop doesn't clip text at the edges,
    # while clamping to image bounds to avoid out-of-range slicing.
    margin = 10
    titleblock_region = {
        'x': max(0, min_x - margin),
        'y': max(0, min_y - margin),
        'width': min(width - (min_x - margin), max_x - min_x + 2 * margin),
        'height': min(height - (min_y - margin), max_y - min_y + 2 * margin)
    }

    return titleblock_region