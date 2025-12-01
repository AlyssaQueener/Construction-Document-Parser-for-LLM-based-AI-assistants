import fitz
import json
import re 
from scipy.spatial import Voronoi
import numpy as np
from collections import defaultdict

def is_number_like(text):
    """Returns True if the block is mostly numeric or appears to be a number with units."""
    text = text.strip().replace(",", ".")
    text = text.replace("\n", " ")
    text = re.sub(r"(m²|m|cm|°|%|\s+|ca|ca.|m2| qm | og| eg| ug| nr| nr.)", "", text, flags=re.IGNORECASE)
    try:
        float(text)
        return True
    except ValueError:
        return False

def has_more_than_one_char(s):
    """Returns True if the cleaned string has more than 2 characters."""
    s = s.strip().replace("\n", "").replace(" ", "")
    if s.upper() == 'WC':
        return True
    return len(s) > 2

def is_valid_room_name(text):
    """Determines if the provided text qualifies as a valid room name."""
    text = text.strip()
    if text.lower() == 'wc':
        return True
    if len(text) < 3:
        return False
    excluded = {'ca', 'ca.', 'cm', 'm²', 'm2', 'qm', 'og', 'eg', 'ug', 'nr', 'nr.', 'no', 'no.', 'plan'}
    if text.lower() in excluded:
        return False
    if text.lower().startswith('architectur'):
        return False
    if not any(c.isalpha() for c in text):
        return False
    letter_count = sum(1 for c in text if c.isalpha())
    if letter_count < 3:
        return False
    return True

def are_close(e1, e2, y_thresh=10, x_thresh=40):
    """Checks if two word-bounding boxes are spatially close."""
    y_close = abs(e1[1] - e2[1]) < y_thresh
    x_close = abs(e1[2] - e2[0]) < x_thresh
    return y_close and x_close

def merge_entries(e1, e2):
    """Merges two word bounding box entries into a single one."""
    x0 = min(e1[0], e2[0])
    y0 = min(e1[1], e2[1])
    x1 = max(e1[2], e2[2])
    y1 = max(e1[3], e2[3])
    text = f"{e1[4]} {e2[4]}"
    return [x0, y0, x1, y1, text, e1[5], e1[6], e1[7]]

def combine_close_words(bboxes):
    """Scans a list of word bboxes and merges spatially-close words."""
    bboxes = sorted(bboxes, key=lambda x: (x[1], x[0]))
    combined = []
    skip_indices = set()
    for i, word1 in enumerate(bboxes):
        if i in skip_indices:
            continue
        merged = word1
        for j in range(i + 1, len(bboxes)):
            if j in skip_indices:
                continue
            word2 = bboxes[j]
            if are_close(merged, word2):
                merged = merge_entries(merged, word2)
                skip_indices.add(j)
        combined.append(merged)
    return combined

def calculate_bbox_center(bbox):
    """Calculates the geometric center of a bounding box."""
    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
    name = bbox[4]
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    return [cx, cy, name]

def flip_y_coordinates(centerpoints, page_height):
    """Converts PyMuPDF Y-coordinates to standard plotting coordinates."""
    flipped_centerpoints = []
    for point in centerpoints:
        cx, cy, name = point[0], point[1], point[2]
        cy_flipped = page_height - cy
        flipped_centerpoints.append([cx, cy_flipped, name])
    return flipped_centerpoints

def extract_bounded_voronoi_neighbors(centerpoints, bounds):
    """Finds Voronoi neighbors for labeled centerpoints."""
    if len(centerpoints) < 3:
        raise ValueError("Need at least 3 points for Voronoi diagram")
    
    points = np.array([[cp[0], cp[1]] for cp in centerpoints])
    names = [cp[2] for cp in centerpoints]
    
    vor = Voronoi(points)
    x_min, y_min, x_max, y_max = bounds
    neighbors_dict = defaultdict(set)
    
    for ridge_idx, ridge_points in enumerate(vor.ridge_points):
        point1_idx, point2_idx = ridge_points
        name1 = names[point1_idx]
        name2 = names[point2_idx]
        ridge_vertices = vor.ridge_vertices[ridge_idx]
        
        if -1 in ridge_vertices:
            finite_idx = ridge_vertices[0] if ridge_vertices[1] == -1 else ridge_vertices[1]
            if finite_idx >= 0:
                finite_v = vor.vertices[finite_idx]
                v_in = x_min <= finite_v[0] <= x_max and y_min <= finite_v[1] <= y_max
                if v_in:
                    neighbors_dict[name1].add(name2)
                    neighbors_dict[name2].add(name1)
        else:
            v1 = vor.vertices[ridge_vertices[0]]
            v2 = vor.vertices[ridge_vertices[1]]
            v1_in = x_min <= v1[0] <= x_max and y_min <= v1[1] <= y_max
            v2_in = x_min <= v2[0] <= x_max and y_min <= v2[1] <= y_max
            midpoint_x = (v1[0] + v2[0]) / 2
            midpoint_y = (v1[1] + v2[1]) / 2
            mid_in = x_min <= midpoint_x <= x_max and y_min <= midpoint_y <= y_max
            if mid_in or v1_in or v2_in:
                neighbors_dict[name1].add(name2)
                neighbors_dict[name2].add(name1)
    
    neighbors = {name: sorted(list(neighs)) for name, neighs in neighbors_dict.items()} 
    return neighbors

def make_names_unique(centerpoints):
    """Makes duplicate room names unique by adding sequential numbers."""
    name_counts = {}
    unique_centerpoints = []
    
    for cp in centerpoints:
        cx, cy, name = cp[0], cp[1], cp[2]
        
        if name in name_counts:
            name_counts[name] += 1
            unique_name = f"{name}_{name_counts[name]}"
        else:
            name_counts[name] = 1
            unique_name = name
        
        unique_centerpoints.append([cx, cy, unique_name])
    
    return unique_centerpoints

def neighboring_rooms_voronoi(pdf_path):
    """
    Extract neighboring rooms from a floorplan PDF using Voronoi diagram.
    
    Args:
        pdf_path: Path to the PDF file to process
        
    Returns:
        str: JSON string mapping room names to their list of neighboring rooms
    """
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Clip rectangle to exclude plan information
    width, height = page.rect.width, page.rect.height
    clip_rect = fitz.Rect(0, 0, width * 0.8, height * 0.8)
    flipped_rect = (
        clip_rect.x0,
        height - clip_rect.y1,
        clip_rect.x1,
        height - clip_rect.y0
    )
    
    # Extract and filter words
    word = page.get_textpage(clip_rect)
    bbox = word.extractWORDS()
    
    filtered_bbox_number = [entry for entry in bbox if not is_number_like(entry[4])]
    filtered_bbox_string_1 = [entry for entry in filtered_bbox_number if is_valid_room_name(entry[4])]
    filtered_bbox_string = [entry for entry in filtered_bbox_string_1 if has_more_than_one_char(entry[4])]
    combined_bbox = combine_close_words(filtered_bbox_string)
    
    # Calculate centerpoints
    centerpoints = []
    for entry in combined_bbox:
        centerpoint = calculate_bbox_center(entry)
        centerpoints.append(centerpoint)
    
    # Create voronoi polygons around the center points
    page_width, page_height = page.rect.width, page.rect.height
    flipped_centerpoints = flip_y_coordinates(centerpoints, page_height)
    flipped_centerpoints = make_names_unique(flipped_centerpoints)
    neighbors = extract_bounded_voronoi_neighbors(flipped_centerpoints, flipped_rect)
    
    doc.close()
    
    # Return as JSON string
    output_json = json.dumps(neighbors, indent=2, ensure_ascii=False)
    return neighbors

if __name__ == "__main__":
    pdf_path = "src/validation/Floorplan/neighboring rooms/Simple Floorplan/Simple Floorplan/01_Simple.pdf"  # Replace with your PDF path
    result = neighboring_rooms_voronoi(pdf_path)
    print(result)