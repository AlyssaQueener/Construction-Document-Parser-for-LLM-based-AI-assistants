import sys
from pathlib import Path

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import fitz
import json
import re 
from scipy.spatial import Voronoi
import matplotlib.pyplot as plt
from scipy.spatial import voronoi_plot_2d
import numpy as np
from collections import defaultdict
import src.plan2data.mistralConnection as mistral
import base64
import pymupdf
import src.plan2data.titleBlockInfo as tb



def convert_pdf_to_base64(pdf_path: str, page: int = 0):
    """
    Convert a specific PDF page to base64-encoded PNG image string.
    
    Used for sending floor plan images to AI vision models for analysis.
    
    Args:
        pdf_path (str): Path to the PDF file
        page (int): Page number to convert (default: 0 for first page)
    
    Returns:
        str: Base64-encoded PNG image as string
    
    Example:
        >>> base64_img = convert_pdf_to_base64("floorplan.pdf")
        >>> # Can now send to vision API
    """
    # Open the document
    pdfIn = pymupdf.open(pdf_path)
    
    # Select the page
    page_obj = pdfIn[page]
    
    # Convert to image at 300 DPI for good quality
    pix = page_obj.get_pixmap(dpi=300)
    
    # Convert to PNG bytes
    img_bytes = pix.pil_tobytes(format="PNG")
    
    # Encode to base64 string
    base64_image = base64.b64encode(img_bytes).decode('utf-8')
    
    pdfIn.close()
    
    return base64_image


def is_number_like(text):
    """
    Check if text appears to be primarily numeric (with optional units).
    
    Used to filter out measurements, coordinates, and other numeric annotations
    from floor plan text extraction.
    
    Args:
        text (str): The text block to analyze
    
    Returns:
        bool: True if text is number-like (e.g., "2.50", "15 m²", "ca. 20"), False otherwise
    
    Examples:
        >>> is_number_like("2.50")
        True
        >>> is_number_like("15 m²")
        True
        >>> is_number_like("Küche")
        False
    """
    # Normalize text: replace commas with periods, remove newlines
    text = text.strip().replace(",", ".")
    text = text.replace("\n", " ")
    
    # Remove common units and measurement terms
    text = re.sub(
        r"(m²|m|cm|°|%|\s+|ca|ca.|m2| qm | og| eg| ug| nr| nr.)", 
        "", 
        text, 
        flags=re.IGNORECASE
    )
    
    # Try to parse as float
    try:
        float(text)
        return True
    except ValueError:
        return False


def is_number_block(text):
    """
    Check if ALL meaningful parts of text are numeric.
    
    Stricter than is_number_like - requires every space-separated component to be numeric.
    
    Args:
        text (str): The concatenated text, potentially with numbers and units
    
    Returns:
        bool: True if every part is number-like, False otherwise
    
    Examples:
        >>> is_number_block("2.50 15.20")
        True
        >>> is_number_block("2.50 Küche")
        False
    """
    # Normalize whitespace
    text = text.replace("\n", " ").strip()
    
    if not text:
        return False
    
    # Split into parts and check each
    parts = text.split()
    for part in parts:
        clean = part.strip().replace(",", ".")
        # Remove common units
        clean = re.sub(r"(m²|m|cm|°|%|\s+)", "", clean, flags=re.IGNORECASE)
        
        # Each part must be parseable as float
        try:
            float(clean)
        except ValueError:
            return False
    
    return True


def has_more_than_one_char(s):
    """
    Check if string has more than 2 meaningful characters (excluding whitespace).
    
    Filters out single-character annotations and very short codes. Special case: "WC" is always valid.
    
    Args:
        s (str): Any input string
    
    Returns:
        bool: True if length > 2 after cleaning, or if string is "WC"
    
    Examples:
        >>> has_more_than_one_char("A")
        False
        >>> has_more_than_one_char("WC")
        True
        >>> has_more_than_one_char("Küche")
        True
    """
    # Remove all whitespace and newlines
    s = s.strip().replace("\n", "").replace(" ", "")
    
    # Special case: WC is always valid
    if s.upper() == 'WC':
        return True
    
    return len(s) > 2


def extract_text_from_pdf(pdf_path, clean=True):
    """
    Extract all text from PDF with optional filtering of numeric and short strings.
    
    Extracts text spans from all pages and optionally filters out measurements,
    coordinates, and technical annotations to focus on room names and labels.
    
    Args:
        pdf_path (str): Path to the input PDF file
        clean (bool): If True, filter out numbers, coordinates, and short strings (default: True)
    
    Returns:
        str: All extracted text concatenated with spaces
    
    Note:
        Prints extraction statistics when clean=True, showing how many elements were filtered.
    """
    doc = fitz.open(pdf_path)
    
    all_text = []
    filtered_count = 0
    total_count = 0
    
    # Process each page
    for page in doc:
        textpage = page.get_textpage()
        text_dict = textpage.extractDICT()
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        total_count += 1
                        
                        if not text:
                            continue
                        
                        if clean:
                            # Filter out numeric content
                            if is_number_like(text) or is_number_block(text):
                                filtered_count += 1
                                continue
                            
                            # Filter out very short strings
                            if not has_more_than_one_char(text):
                                filtered_count += 1
                                continue
                        
                        all_text.append(text)
    
    doc.close()
    
    # Print extraction statistics
    if clean:
        print(f"📊 Text Extraction Statistics:")
        print(f"   Total found: {total_count}")
        print(f"   Filtered out: {filtered_count}")
        print(f"   Sent to AI: {len(all_text)}")
        print(f"   Filter rate: {(filtered_count/total_count*100):.1f}%\n")
    
    # Join all text with spaces
    return " ".join(all_text)


def ai_roomnames_from_pdf(pdf_path):
    """
    Extract room names from PDF using AI (Mistral).
    
    Extracts and cleans text from PDF, then sends to Mistral AI to identify
    which text elements are actual room names vs. technical annotations.
    
    Args:
        pdf_path (str): Path to the floor plan PDF
    
    Returns:
        list: List of identified room names from AI
    
    Note:
        Prints text extraction statistics and first 500 characters sent to AI.
    """
    # Extract and clean text
    text = extract_text_from_pdf(pdf_path, clean=True)
    
    # Validation
    if not text or text.strip() == "":
        print("⚠️  Warning: No text extracted from PDF after filtering")
        return []
    
    print(f"📝 Sending {len(text)} characters to Mistral AI...")
    print(f"📄 First 500 characters of text:")
    print("-" * 80)
    print(text[:500])
    print("-" * 80)
    print()
    
    # Send to AI
    room_names_ai = mistral.call_mistral_roomnames(text)
    
    print(f"🤖 AI Response: {room_names_ai}")
    print(f"📊 Number of rooms found: {len(room_names_ai)}")
    
    return room_names_ai


def is_valid_room_name(text, room_names_ai=None):
    """
    Validate if text is a legitimate room name, filtering out technical terms.
    
    Uses extensive exclusion list and pattern matching to distinguish room names
    from measurements, floor indicators, technical codes, and plan annotations.
    
    Args:
        text (str): The text to validate
        room_names_ai (list, optional): List of room names identified by AI for reference
    
    Returns:
        bool: True if valid room name, False otherwise
    
    Filtering strategy:
        1. Check against exclusion list (units, floor codes, technical terms)
        2. Reject pure numbers and coordinates
        3. Reject technical codes (e.g., "DN 100")
        4. If AI list provided: accept only if in AI list (strict mode)
        5. Otherwise: keyword matching for common room terms
    
    Examples:
        >>> is_valid_room_name("Küche")
        True
        >>> is_valid_room_name("2.50")
        False
        >>> is_valid_room_name("1.OG")
        False
        >>> is_valid_room_name("WC")
        True
    """
    # Comprehensive exclusion list
    excluded = {
        # Units and measurements
        'ca', 'ca.', 'cm', 'm²', 'm2', 'qm', 'mm', 'dm',
        # Floor indicators
        'og', 'eg', 'ug', 'dg', 'kg', '1.og', '2.og', 'brh',
        # Notes and additional information
        'nts', 'abb.', 'abb', 'allg', 'allg.', 'bes.', 'bes', 'bez.', 'bez', 
        'bezg', 'brh', 'stg',
        # Numbers and references
        'nr', 'nr.', 'no', 'no.', 'pos', 'pos.',
        # Plan terms
        'plan', 'detail', 'schnitt', 'ansicht', 'grundriss', 'fläche', 
        'maßstab', 'massstab', 'zimmertüren', 'türen', 'raumnummer', 'heizung', 'fußboden',
        'fußbodenheizung', 'lüftung', 'fenster', 'tür', 'türen', 'wand', 'wände',
        'installation', 'installationen', 'dämmung', 'dämmstoffe',
        # Scales
        '1:50', '1:100', '1:200', '1:500',
        # Technical abbreviations
        'dn', 'nw', 'dia', 'durchm.',
        # Administrative terms
        'datum', 'gepr', 'gez', 'bearb', 'index',
        # Cardinal directions
        'nord', 'süd', 'ost', 'west', 'n', 's', 'o', 'w',
        # Axis labels
        'achse', 'raster',
    }
    
    # Basic validation
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip()
    
    # Empty strings rejected
    if not text:
        return False
    
    # Special case: WC is always valid
    if text.upper() == 'WC':
        return True
    
    # CRITICAL: Check exclusion list FIRST
    if text.lower() in excluded:
        return False
    
    # Reject pure numbers or coordinates (e.g., "1.50", "12.5", "2.40")
    # But allow room numbers like "Raum 1.01", "Zimmer 2"
    if re.match(r'^[\d.,]+$', text):
        return False
    
    # Reject technical codes (e.g., "DN 100", "Ø 50")
    # Exception: Room numbers like "Z1", "R2.1" are OK
    if re.match(r'^[A-Z]{1,3}\s*\d+', text, re.IGNORECASE):
        if not re.match(r'^[ZR]\d', text, re.IGNORECASE):
            return False
    
    # If AI provided a list, use strict matching
    expanded_names = []
    if room_names_ai:
        # Normalize AI names: strip, lowercase, exclude blacklisted
        valid_ai_names = {
            name.strip().lower() 
            for name in room_names_ai 
            if name.strip().lower() not in excluded
        }
        
        # Expand AI names to include components
        for name in valid_ai_names:
            expanded_names.append(name)
            # Add split components if there are spaces
            if ' ' in name:
                components = name.split()
                for comp in components:
                    expanded_names.append(comp)
        
        # If text is in the expanded AI list, accept it
        if text.lower() in expanded_names:
            return True
        else:
            # Strict mode: reject if not in AI list
            return False
    
    print(f"Filtered room names: {expanded_names}")
    
    # Fallback if no AI list: keyword matching
    room_keywords = [
        'zimmer', 'raum', 'bad', 'wc', 'küche', 'keller', 'diele', 'flur',
        'wohn', 'schlaf', 'kind', 'gäste', 'arbeit', 'arbeits', 'büro', 'ess',
        'abstell', 'hauswirtschaft', 'hwr', 'technik', 'heizung',
        'garage', 'carport', 'terrasse', 'balkon', 'loggia',
        'eingang', 'windfang', 'vorraum', 'ankleide', 'schrank'
    ]
    
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in room_keywords):
        return True
    
    return False


def are_close(e1, e2, y_thresh=10, x_thresh=40):
    """
    Check if two word bounding boxes are spatially close enough to merge.
    
    Used to combine multi-word room names that were split by PDF text extraction.
    
    Args:
        e1 (list or tuple): [x0, y0, x1, y1, ...] coordinates for first box
        e2 (list or tuple): [x0, y0, x1, y1, ...] coordinates for second box
        y_thresh (float): Max vertical distance to consider close (default: 10)
        x_thresh (float): Max horizontal distance to consider close (default: 40)
    
    Returns:
        bool: True if boxes are close enough to be part of same room name
    
    Logic:
        Two boxes are "close" if:
        - Their Y-coordinates differ by less than y_thresh (same line)
        - Their X-coordinates differ by less than x_thresh (nearby horizontally)
    """
    y_close = abs(e1[1] - e2[1]) < y_thresh  # Vertical proximity
    x_close = abs(e1[2] - e2[0]) < x_thresh  # Horizontal proximity
    return y_close and x_close


def merge_entries(e1, e2):
    """
    Merge two word bounding box entries into a single combined entry.
    
    Concatenates text and creates bounding box that encompasses both entries.
    
    Args:
        e1 (list): Entry 1 as [x0, y0, x1, y1, text, block_no, line_no, word_no]
        e2 (list): Entry 2, same structure
    
    Returns:
        list: Merged entry [x0, y0, x1, y1, combined_text, block_no, line_no, word_no]
    
    Example:
        >>> e1 = [10, 20, 30, 40, "Wohn", 1, 1, 1]
        >>> e2 = [32, 20, 60, 40, "zimmer", 1, 1, 2]
        >>> merge_entries(e1, e2)
        [10, 20, 60, 40, "Wohn zimmer", 1, 1, 1]
    """
    # Create bounding box that encompasses both
    x0 = min(e1[0], e2[0])
    y0 = min(e1[1], e2[1])
    x1 = max(e1[2], e2[2])
    y1 = max(e1[3], e2[3])
    
    # Concatenate text with space
    text = f"{e1[4]} {e2[4]}"
    
    # Keep metadata from first entry
    return [x0, y0, x1, y1, text, e1[5], e1[6], e1[7]]


def combine_close_words(bboxes):
    """
    Scan list of word bboxes and merge spatially-close words into phrases.
    
    Iteratively combines words that are close together to reconstruct multi-word
    room names like "Wohn zimmer" or "Kinder zimmer".
    
    Args:
        bboxes (list of list): Each entry is [x0, y0, x1, y1, text, block_no, line_no, word_no]
    
    Returns:
        list of list: Combined word bboxes with merged multi-word phrases
    
    Algorithm:
        1. Sort bboxes by position (top-to-bottom, left-to-right)
        2. For each word, check following words for proximity
        3. Merge all close words into single entry
        4. Track merged indices to avoid duplicates
    """
    # Sort by position: top to bottom, left to right
    bboxes = sorted(bboxes, key=lambda x: (x[1], x[0]))
    
    combined = []
    skip_indices = set()
    
    for i, word1 in enumerate(bboxes):
        if i in skip_indices:
            continue
        
        merged = word1
        
        # Check all following words for proximity
        for j in range(i + 1, len(bboxes)):
            if j in skip_indices:
                continue
            
            word2 = bboxes[j]
            
            # If close, merge and mark as processed
            if are_close(merged, word2):
                merged = merge_entries(merged, word2)
                skip_indices.add(j)
        
        combined.append(merged)
    
    return combined


def calculate_bbox_center(bbox):
    """
    Calculate the geometric center point of a bounding box.
    
    Args:
        bbox (list): [x0, y0, x1, y1, name, ...]
    
    Returns:
        list: [center_x, center_y, name] representing the centerpoint
    
    Example:
        >>> bbox = [10, 20, 50, 60, "Küche"]
        >>> calculate_bbox_center(bbox)
        [30.0, 40.0, "Küche"]
    """
    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
    name = bbox[4]
    
    # Calculate center
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    
    return [cx, cy, name]


def flip_y_coordinates(centerpoints, page_height):
    """
    Convert PyMuPDF Y-coordinates to standard plotting coordinates.
    
    PyMuPDF uses origin at top-left with Y increasing downward.
    This flips to origin at bottom-left with Y increasing upward (standard math coordinates).
    
    Args:
        centerpoints (list of list): [cx, cy, name] center point data
        page_height (float): Height of the PDF page
    
    Returns:
        list of list: Each [cx, flipped_cy, name] with corrected Y-coordinate
    
    Transform:
        y_flipped = page_height - y_original
    """
    flipped_centerpoints = []
    
    for point in centerpoints:
        cx, cy, name = point[0], point[1], point[2]
        
        # Flip Y-coordinate
        cy_flipped = page_height - cy
        
        flipped_centerpoints.append([cx, cy_flipped, name])
    
    return flipped_centerpoints


def extract_bounded_voronoi_neighbors_detailed(centerpoints, bounds):
    """
    Find neighboring rooms using Voronoi diagram with boundary constraints.
    
    Creates Voronoi tessellation of room centerpoints and identifies which rooms
    share Voronoi cell boundaries (indicating adjacency). Only includes edges
    within the specified bounds to exclude spurious connections at document edges.
    
    Args:
        centerpoints (list of list): [cx, cy, name] for all room centerpoints
        bounds (tuple or list): (x_min, y_min, x_max, y_max) bounding box
    
    Returns:
        tuple: (neighbors_dict, vor)
            - neighbors_dict (dict): room name → list of neighbor names
            - vor (scipy.spatial.Voronoi): Voronoi diagram object
    
    Algorithm:
        1. Create Voronoi diagram from room centerpoints
        2. For each Voronoi ridge (cell boundary):
           - Check if ridge vertices are within bounds
           - If yes, mark the two rooms as neighbors
        3. Handle infinite ridges (extending to infinity) specially
    
    Raises:
        ValueError: If fewer than 3 points provided (minimum for Voronoi)
    
    Note:
        Filters out edges outside bounds to prevent false adjacencies
        at title block or document margins.
    """
    if len(centerpoints) < 3:
        raise ValueError("Need at least 3 points for Voronoi diagram")
    
    # Extract points and names
    points = np.array([[cp[0], cp[1]] for cp in centerpoints])
    names = [cp[2] for cp in centerpoints]
    
    # Create Voronoi diagram
    vor = Voronoi(points)
    
    # Unpack bounds
    x_min, y_min, x_max, y_max = bounds
    
    neighbors_dict = defaultdict(set)
    
    # Process each Voronoi ridge (boundary between two cells)
    for ridge_idx, ridge_points in enumerate(vor.ridge_points):
        point1_idx, point2_idx = ridge_points
        name1 = names[point1_idx]
        name2 = names[point2_idx]
        
        ridge_vertices = vor.ridge_vertices[ridge_idx]
        
        # Handle infinite ridges (extending to infinity)
        if -1 in ridge_vertices:
            # Get the finite vertex
            finite_idx = ridge_vertices[0] if ridge_vertices[1] == -1 else ridge_vertices[1]
            
            if finite_idx >= 0:
                finite_v = vor.vertices[finite_idx]
                
                # Check if finite vertex is within bounds
                v_in = x_min <= finite_v[0] <= x_max and y_min <= finite_v[1] <= y_max
                
                if v_in:
                    neighbors_dict[name1].add(name2)
                    neighbors_dict[name2].add(name1)
        else:
            # Both vertices are finite
            v1 = vor.vertices[ridge_vertices[0]]
            v2 = vor.vertices[ridge_vertices[1]]
            
            # Check if vertices are within bounds
            v1_in = x_min <= v1[0] <= x_max and y_min <= v1[1] <= y_max
            v2_in = x_min <= v2[0] <= x_max and y_min <= v2[1] <= y_max
            
            # Calculate midpoint
            midpoint_x = (v1[0] + v2[0]) / 2
            midpoint_y = (v1[1] + v2[1]) / 2
            mid_in = x_min <= midpoint_x <= x_max and y_min <= midpoint_y <= y_max
            
            # If any point is within bounds, consider as valid neighbor relationship
            if mid_in or v1_in or v2_in:
                neighbors_dict[name1].add(name2)
                neighbors_dict[name2].add(name1)
    
    # Convert sets to sorted lists
    neighbors = {name: sorted(list(neighs)) for name, neighs in neighbors_dict.items()}
    
    return neighbors, vor


def make_names_unique(centerpoints):
    """
    Make duplicate room names unique by adding sequential numbers.
    
    When multiple rooms have the same name (e.g., multiple "Bad" rooms),
    adds numerical suffixes to distinguish them (Bad_1, Bad_2, etc.).
    Names are numbered based on left-to-right position.
    
    Args:
        centerpoints (list of list): [cx, cy, name] for all rooms
    
    Returns:
        list of list: Modified centerpoints with unique names
    
    Example:
        >>> cp = [[10, 20, "Bad"], [50, 20, "Bad"], [30, 20, "Küche"]]
        >>> make_names_unique(cp)
        [[10, 20, "Bad"], [50, 20, "Bad_2"], [30, 20, "Küche"]]
    """
    name_counts = {}
    unique_centerpoints = []
    
    # Sort by x-coordinate (left to right) for consistent numbering
    centerpoints = sorted(centerpoints, key=lambda cp: cp[0])
    
    for cp in centerpoints:
        cx, cy, name = cp[0], cp[1], cp[2]
        
        # Check if this name already exists
        if name in name_counts:
            name_counts[name] += 1
            unique_name = f"{name}_{name_counts[name]}"
        else:
            name_counts[name] = 1
            unique_name = name
        
        unique_centerpoints.append([cx, cy, unique_name])
    
    return unique_centerpoints


def add_indices_to_neighbors(neighbors, centerpoints):
    """
    Add positional indices to neighbor relationships for duplicate room names.
    
    Enhances neighbor data by tracking which specific instance of a duplicated
    room name each relationship refers to (e.g., "Bad_#1", "Bad_#2").
    
    Args:
        neighbors (dict): room name → list of neighbor names
        centerpoints (list of list): [cx, cy, name] for all rooms
    
    Returns:
        dict: Enhanced neighbor data with indices and coordinates for duplicate names
              Format: {
                  "unique_room": {"neighbors": [...], "coordinates": [x, y]},
                  "duplicate_#1": {"original_name": "...", "position_index": 1, ...}
              }
    
    Note:
        Currently not used in main pipeline but available for enhanced analysis.
    """
    # Sort centerpoints left to right
    sorted_cp = sorted(enumerate(centerpoints), key=lambda x: x[1][0])
    
    # Map original indices to left-to-right position for each room name
    name_to_indices = defaultdict(list)
    for lr_idx, (orig_idx, cp) in enumerate(sorted_cp):
        name = cp[2]
        name_to_indices[name].append({
            'original_index': orig_idx,
            'left_right_index': len(name_to_indices[name]) + 1,
            'coordinates': [cp[0], cp[1]]
        })
    
    # Build enhanced output
    enhanced_neighbors = {}
    for name, neighs in neighbors.items():
        instances = name_to_indices[name]
        
        if len(instances) == 1:
            # Single instance - no index needed
            enhanced_neighbors[name] = {
                'neighbors': neighs,
                'coordinates': instances[0]['coordinates']
            }
        else:
            # Multiple instances - add indexed entries
            for inst in instances:
                indexed_name = f"{name}_#{inst['left_right_index']}"
                enhanced_neighbors[indexed_name] = {
                    'original_name': name,
                    'position_index': inst['left_right_index'],
                    'coordinates': inst['coordinates'],
                    'neighbors': neighs
                }
    
    return enhanced_neighbors


def neighboring_rooms_voronoi(pdf_path):
    """
    Extract neighboring room relationships from floor plan PDF using Voronoi analysis.
    
    Complete pipeline:
    1. Extract room names using AI
    2. Extract text bounding boxes from PDF
    3. Filter to valid room names only
    4. Combine multi-word room names
    5. Calculate room centerpoints
    6. Create Voronoi diagram
    7. Identify neighboring rooms from shared Voronoi edges
    
    Args:
        pdf_path (str): Path to the PDF floor plan file
    
    Returns:
        dict: Dictionary mapping room names to lists of neighboring room names
              Format: {"Küche": ["Wohnzimmer", "Flur"], "Bad": ["Flur"], ...}
    
    Algorithm:
        Uses Voronoi tessellation as a proxy for room adjacency - rooms whose
        centerpoints create adjacent Voronoi cells are likely to be neighboring
        rooms on the floor plan.
    """
    # Get AI-identified room names
    room_names_ai = ai_roomnames_from_pdf(pdf_path)
    
    # Open PDF
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Define clip rectangle to exclude title block and margins
    # Use 80% of width to exclude right-side plan information
    width, height = page.rect.width, page.rect.height
    clip_rect = fitz.Rect(0, 0, width * 0.8, height)
    
    # Create flipped rectangle for Voronoi bounds (in flipped coordinates)
    flipped_rect = (
        clip_rect.x0,
        height - clip_rect.y1,
        clip_rect.x1,
        height - clip_rect.y0
    )
    
    # Extract words from clipped region
    word = page.get_textpage(clip_rect)
    bbox = word.extractWORDS()
    
    # Filter 1: Valid room names (using AI list)
    filtered_bbox_string_1 = [
        entry for entry in bbox 
        if is_valid_room_name(entry[4], room_names_ai)
    ]
    
    # Combine spatially close words (multi-word room names)
    combined_bbox = combine_close_words(filtered_bbox_string_1)
    
    # Filter 2: Remove numeric entries
    filtered_bbox_number = [
        entry for entry in combined_bbox 
        if not is_number_like(entry[4])
    ]
    
    # Filter 3: Remove very short strings
    filtered_bbox_string = [
        entry for entry in filtered_bbox_number 
        if has_more_than_one_char(entry[4])
    ]
    
    # Calculate centerpoints for each room name
    centerpoints = []
    for entry in filtered_bbox_string:
        centerpoint = calculate_bbox_center(entry)
        centerpoints.append(centerpoint)
    
    # Flip Y-coordinates to standard math coordinates
    page_width, page_height = page.rect.width, page.rect.height
    flipped_centerpoints = flip_y_coordinates(centerpoints, page_height)
    
    # Make duplicate names unique
    flipped_centerpoints = make_names_unique(flipped_centerpoints)
    
    # Create Voronoi diagram and extract neighbors
    neighbors, vor = extract_bounded_voronoi_neighbors_detailed(
        flipped_centerpoints, 
        flipped_rect
    )
    
    doc.close()
    
    return neighbors

def visualize_voronoi_cells(vor, centerpoints, neighbors, save_path=None):
    """
    Visualizes Voronoi diagram using centerpoints and optionally saves as an image.

    Args:
        vor (scipy.spatial.Voronoi): Voronoi object.
        centerpoints (list of list): [cx, cy, name] labels.
        neighbors (dict): room name to neighbor room names.
        save_path (str, optional): If provided, image is saved to this file path.

    Returns:
        None
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    voronoi_plot_2d(vor, ax=ax, show_vertices=False, line_colors='blue', line_width=2)
    for i, cp in enumerate(centerpoints):
        ax.plot(cp[0], cp[1], 'ro', markersize=8)
        ax.text(cp[0], cp[1], cp[2], fontsize=10, ha='center', va='bottom', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    ax.set_title('Voronoi Diagram - Room Adjacencies', fontsize=14)
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.grid(True, alpha=0.3)
    total_connections = sum(len(neighs) for neighs in neighbors.values()) // 2
    ax.text(0.02, 0.98, f'Total room connections: {total_connections}',
            transform=ax.transAxes, fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

def extract_full_floorplan(pdf_path):
    """
    Extract complete floor plan data: neighboring rooms and actual connections.
    
    Combines Voronoi-based neighbor detection with AI vision analysis to
    determine which room pairs are actually connected (share a doorway).
    
    Pipeline:
    1. Run Voronoi analysis to identify potential neighbors
    2. Convert PDF page to base64 image
    3. Send image + neighbor candidates to Mistral vision model
    4. AI identifies which neighbor pairs have actual doorway connections
    5. Combine all data into structured JSON output
    
    Args:
        pdf_path (str): Path to the PDF floor plan file
    
    Returns:
        str: JSON string containing:
             {
                 "neighboring_rooms": {room: [neighbors]},
                 "connected_rooms": {room: [connected_neighbors]}
             }
    
    Note:
        "neighboring_rooms" = spatial proximity (Voronoi)
        "connected_rooms" = actual doorway connections (AI vision)
    
    Example output:
        {
            "neighboring_rooms": {
                "Küche": ["Wohnzimmer", "Flur"],
                "Bad": ["Flur"]
            },
            "connected_rooms": {
                "Küche": ["Wohnzimmer"],  # No door to Flur
                "Bad": ["Flur"]
            }
        }
    """
    try:
        # 1. Get neighboring rooms from Voronoi analysis
        print("🔍 Step 1: Getting Voronoi neighbors...")
        neighbors_vor = neighboring_rooms_voronoi(pdf_path)
        print(f"✅ Got neighbors: {type(neighbors_vor)}")
        
        print("🔍 Step 2: Converting to dict...")
        if isinstance(neighbors_vor, str):
            neighbors_vor = json.loads(neighbors_vor)
        print(f"✅ Neighbors dict: {neighbors_vor}")
        
        print("🔍 Step 3: Converting PDF to base64...")
        base64_image = convert_pdf_to_base64(pdf_path)
        print(f"✅ Got base64 image: {len(base64_image)} characters")
        
        print("🔍 Step 4: Calling Mistral API...")
        connected_rooms_response = mistral.call_mistral_connected_rooms(
            base64_image, 
            json.dumps(neighbors_vor)
        )
        print(f"✅ Got Mistral response: {type(connected_rooms_response)}")
        
        print("🔍 Step 5: Parsing response...")
        if isinstance(connected_rooms_response, str):
            connected_rooms = json.loads(connected_rooms_response)
        else:
            connected_rooms = connected_rooms_response
        print(f"✅ Connected rooms: {connected_rooms}")
        
        # 6. Combine all outputs into single dictionary
        full_floorplan = {
            # "titleblock": titleblock,  # Uncomment if using title block extraction
            "neighboring_rooms": neighbors_vor,
            "connected_rooms": connected_rooms
        }
        
        # 7. Pretty-print output
        formatted_output = json.dumps(full_floorplan, indent=2, ensure_ascii=False)
        print("\n📋 Full Floorplan Data:")
        print(formatted_output)
        return full_floorplan
    
    except Exception as e:
        print(f"❌ Error in AI analysis: {e}")
        import traceback
        traceback.print_exc()
        
        # Return partial results if Voronoi succeeded but AI failed
        if 'neighbors_vor' in locals():
            print("⚠️ Returning partial results (Voronoi only, no AI connections)")
            partial_result = {
                "neighboring_rooms": neighbors_vor,
                "connected_rooms": {},  # Empty - AI call failed
                "error": "AI vision analysis unavailable due to rate limits",
                "note": "neighboring_rooms shows spatial proximity (Voronoi only)"
            }
            return partial_result
        
        # If Voronoi also failed, return empty
        return "{}"


if __name__ == "__main__":
    # Test files
    # pdf_path = "src/validation/Floorplan/titleblock/testdata/floorplan-test-2.pdf" 
    #pdf_path = "src/validation/Floorplan/neighboring rooms/Simple Floorplan/Simple Floorplan/01_Simple.pdf" 
    
    pdf_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf.pdf"
    #connected_rooms = extract_full_floorplan(pdf_path)
    neighboring_rooms_voronoi(pdf_path)
    print(pdf_path)
