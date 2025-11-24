import os
import fitz
import json
import re 
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def is_number_like(text):
    """
    Returns True if the block is mostly numeric or appears to be a number with units.

    Args:
        text (str): The text block to analyze.

    Returns:
        bool: True if the text can be interpreted as mostly number-like, False otherwise.
    """
    text = text.strip().replace(",", ".")
    text = text.replace("\n", " ")
    text = re.sub(r"(m²|m|cm|°|%|\s+|ca|ca.|m2| qm | og| eg| ug| nr| nr.)", "", text, flags=re.IGNORECASE)
    try:
        float(text)
        return True
    except ValueError:
        return False

def is_number_block(text):
    """
    Returns True if ALL meaningful parts of the text are numeric.

    Args:
        text (str): The concatenated text, potentially with numbers and units.

    Returns:
        bool: True if every part is number-like, False otherwise.
    """
    text = text.replace("\n", " ").strip()
    if not text:
        return False
    parts = text.split()
    for part in parts:
        clean = part.strip().replace(",", ".")
        clean = re.sub(r"(m²|m|cm|°|%|\s+)", "", clean, flags=re.IGNORECASE)
        try:
            float(clean)
        except ValueError:
            return False
    return True

def has_more_than_one_char(s):
    """
    Returns True if the cleaned string has more than 2 characters.

    Args:
        s (str): Any input string.

    Returns:
        bool: True if the length after whitespace and newline stripping exceeds 2, False otherwise.
    """
    s = s.strip().replace("\n", "").replace(" ", "")
    return len(s) > 2

def is_valid_room_name(text):
    """
    Determines if the provided text qualifies as a valid room name.

    Args:
        text (str): The text candidate for a room name.

    Returns:
        bool: True if considered a valid room name, False otherwise.
    """
    text = text.strip()
    if len(text) < 3:
        return False
    excluded = {'ca', 'ca.', 'cm', 'm²', 'm2', 'qm', 'og', 'eg', 'ug', 'nr', 'nr.', 'wc'}
    if text.lower() in excluded:
        return False
    if not any(c.isalpha() for c in text):
        return False
    letter_count = sum(1 for c in text if c.isalpha())
    if letter_count < 3:
        return False
    return True

def are_close(e1, e2, y_thresh=10, x_thresh=40):
    """
    Checks if two word-bounding boxes are spatially close.

    Args:
        e1 (list or tuple of float): [x0, y0, x1, y1, ...] coordinates for the first box.
        e2 (list or tuple of float): [x0, y0, x1, y1, ...] coordinates for the second box.
        y_thresh (float, optional): Max allowed y difference to consider as close. Default: 10.
        x_thresh (float, optional): Max allowed x difference. Default: 40.

    Returns:
        bool: True if e1 and e2 are spatially close; otherwise False.
    """
    y_close = abs(e1[1] - e2[1]) < y_thresh
    x_close = abs(e1[2] - e2[0]) < x_thresh
    return y_close and x_close

def merge_entries(e1, e2):
    """
    Merges two word bounding box entries into a single one, concatenating text and combining the box.

    Args:
        e1 (list): Entry 1 [x0, y0, x1, y1, text, block_no, line_no, word_no].
        e2 (list): Entry 2, same structure.

    Returns:
        list: Merged entry as [x0, y0, x1, y1, combined_text, block_no, line_no, word_no].
    """
    x0 = min(e1[0], e2[0])
    y0 = min(e1[1], e2[1])
    x1 = max(e1[2], e2[2])
    y1 = max(e1[3], e2[3])
    text = f"{e1[4]} {e2[4]}"
    return [x0, y0, x1, y1, text, e1[5], e1[6], e1[7]]

def combine_close_words(bboxes):
    """
    Scans a list of word bboxes and merges spatially-close words.

    Args:
        bboxes (list of list): Each list is [x0, y0, x1, y1, text, block_no, line_no, word_no].

    Returns:
        list of list: Combined word bboxes.
    """
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
    """
    Calculates the geometric center of a bounding box.

    Args:
        bbox (list): [x0, y0, x1, y1, name, ...]

    Returns:
        list: [center_x, center_y, name] (float, float, str).
    """
    x1=bbox[0]
    y1=bbox[1]
    x2=bbox[2]
    y2=bbox[3]
    name = bbox[4]
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    center_point=[cx,cy,name]
    return center_point

def flip_y_coordinates(centerpoints, page_height):
    """
    Converts PyMuPDF Y-coordinates to standard plotting coordinates by flipping over the Y axis.

    Args:
        centerpoints (list of list): [cx, cy, name] center point data.
        page_height (float): Height of the page.

    Returns:
        list of list: Each [cx, flipped_cy, name].
    """
    flipped_centerpoints = []
    for point in centerpoints:
        cx, cy, name = point[0], point[1], point[2]
        cy_flipped = page_height - cy
        flipped_centerpoints.append([cx, cy_flipped, name])
    return flipped_centerpoints

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

def print_neighbors_summary(neighbors):
    """
    Prints a summary of room neighbors to the console.

    Args:
        neighbors (dict): room name to list of neighbor room names.

    Returns:
        None
    """
    print("\n=== ROOM NEIGHBORS ===")
    for room, room_neighbors in neighbors.items():
        print(f"{room}: {', '.join(room_neighbors)}")

def save_neighbors_only(neighbors, filename):
    """
    Saves neighbor relationships to a JSON file.

    Args:
        neighbors (dict): room name to neighbor list.
        filename (str): Output JSON file location.

    Returns:
        None
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(neighbors, f, indent=2, ensure_ascii=False)
    print(f"Neighbors saved to '{filename}'")

def analyze_room_connectivity(neighbors):
    """
    Prints analysis of room connectivity including stats, ordering, and most/least connected rooms.

    Args:
        neighbors (dict): room name to neighbor list.

    Returns:
        None
    """
    print("\n=== CONNECTIVITY ANALYSIS ===")
    connection_counts = {room: len(neighs) for room, neighs in neighbors.items()}
    most_connected = max(connection_counts, key=connection_counts.get)
    print(f"Most connected room: {most_connected} ({connection_counts[most_connected]} connections)")
    least_connected = min(connection_counts, key=connection_counts.get)
    print(f"Least connected room: {least_connected} ({connection_counts[least_connected]} connections)")
    avg_connections = sum(connection_counts.values()) / len(connection_counts)
    print(f"Average connections per room: {avg_connections:.1f}")
    sorted_rooms = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)
    print(f"\nRooms by connectivity:")
    for room, count in sorted_rooms:
        print(f"  {room}: {count} connections")

def extract_bounded_voronoi_neighbors_detailed(centerpoints, bounds):
    """
    Finds Voronoi neighbors for labeled centerpoints; details ridge acceptance; supports floorplan boundary.

    Args:
        centerpoints (list of list): [cx, cy, name], all room centerpoints.
        bounds (tuple or list): (x_min, y_min, x_max, y_max) bounding box.

    Returns:
        tuple: (neighbors_dict, vor)
            neighbors_dict (dict): room name to list of neighbor names.
            vor (scipy.spatial.Voronoi): Voronoi diagram object.
    """
    if len(centerpoints) < 3:
        raise ValueError("Need at least 3 points for Voronoi diagram")
    points = np.array([[cp[0], cp[1]] for cp in centerpoints])
    names = [cp[2] for cp in centerpoints]
    #print(f"\n=== ROOM POSITIONS ===")
    #for i, (cp, name) in enumerate(zip(centerpoints, names)):
        #print(f"{name}: ({cp[0]:.1f}, {cp[1]:.1f})")
    vor = Voronoi(points)
    x_min, y_min, x_max, y_max = bounds
    neighbors_dict = defaultdict(set)
    #print(f"\n=== PROCESSING RIDGES ===")
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
                    #print(f"   ✓ ADDED")
                #else:
                    #print(f"   ✗ REJECTED (vertex outside bounds)")
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
                #print(f"   ✓ ADDED")
            #else:
                #print(f"   ✗ REJECTED (all points outside bounds)")
    neighbors = {name: sorted(list(neighs)) for name, neighs in neighbors_dict.items()} 
    return neighbors, vor

def process_simple_voronoi(centerpoints, bounds):
    """
    Performs neighbor extraction, saves to file, prints & visualizes results for labeled rooms.

    Args:
        centerpoints (list of list): [cx, cy, name] for all rooms.
        bounds (tuple or list): (x_min, y_min, x_max, y_max) bounding box.

    Returns:
        tuple: (neighbors_dict, vor)
            neighbors_dict (dict): room name to neighbor list, or None if error.
            vor (scipy.spatial.Voronoi): Voronoi diagram object, or None if error.
    """
    try:
        #print(f"Processing {len(centerpoints)} rooms...")
        neighbors, vor = extract_bounded_voronoi_neighbors_detailed(centerpoints, bounds)
        #save_neighbors_only(neighbors)
        #print_neighbors_summary(neighbors)
        #analyze_room_connectivity(neighbors)
        visualize_voronoi_cells(vor, centerpoints, neighbors, "voronoi_cells.png")
        return neighbors, vor
    except Exception as e:
        print(f"Error processing Voronoi: {e}")
        return None, None
def neighboring_rooms_voronoi(pdf_path):
    """
    Extract neighboring rooms from a floorplan PDF using Voronoi diagram.
    
    Args:
        pdf_path: Path to the PDF file to process
        
    Returns:
        dict: Dictionary mapping room names to their list of neighboring rooms
    """
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Clip rectangle to exclude plan information
    width, height = page.rect.width, page.rect.height
    clip_rect = fitz.Rect(0, 0, width * 0.72, height * 0.8)
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
    neighbors, vor = extract_bounded_voronoi_neighbors_detailed(flipped_centerpoints, flipped_rect)
    
    doc.close()
    
    # Print as JSON and return
    output_json = json.dumps(neighbors, indent=2, ensure_ascii=False)
    return output_json



