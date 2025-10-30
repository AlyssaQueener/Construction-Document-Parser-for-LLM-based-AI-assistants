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
    Returns True if the block is mostly numeric or appears to be a number with units (e.g. "13,5", "12 m²").
    """
    text = text.strip().replace(",", ".")
    text = text.replace("\n", " ")  # Normalize multi-line blocks
    # Remove common units and symbols
    text = re.sub(r"(m²|m|cm|°|%|\s+)", "", text, flags=re.IGNORECASE)
    # Check if it's a pure number now
    try:
        float(text)
        return True
    except ValueError:
        return False

def is_number_block(text):
    """
    Returns True if ALL meaningful parts of the text are numeric.
    For example: "5,4 0,31 2,2" → True; "Küche 13,5" → False
    """
    text = text.replace("\n", " ").strip()
    if not text:
        return False

    # Split into parts (words)
    parts = text.split()

    # Check if every part is a number (after removing units/symbols)
    for part in parts:
        clean = part.strip().replace(",", ".")
        clean = re.sub(r"(m²|m|cm|°|%|\s+)", "", clean, flags=re.IGNORECASE)
        try:
            float(clean)
        except ValueError:
            return False  # If any part is not a number, this is not a number block
    return True
    
def has_more_than_one_char(s):
    s = s.strip().replace("\n", "").replace(" ", "")
    return len(s) > 2

 
    

def are_close(e1, e2, y_thresh=10, x_thresh=40):
    """Check if two words are close enough to be merged (line-wise or block-wise)."""
    # Vertical overlap or proximity
    y_close = abs(e1[1] - e2[1]) < y_thresh
    x_close = abs(e1[2] - e2[0]) < x_thresh
    return y_close and x_close

def merge_entries(e1, e2): # returns a list [x0, y0, x1, y1, "text", block_no, line_no, word_no]
    """Merge two bbox entries into one."""
    x0 = min(e1[0], e2[0])
    y0 = min(e1[1], e2[1])
    x1 = max(e1[2], e2[2])
    y1 = max(e1[3], e2[3])
    text = f"{e1[4]} {e2[4]}"
    return [x0, y0, x1, y1, text, e1[5], e1[6], e1[7]]  # keeping metadata from first

def combine_close_words(bboxes):
    bboxes = sorted(bboxes, key=lambda x: (x[1], x[0]))  # sort by y, then x
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
    Calculate the center point of a bounding box.
    Returns:
        tuple: Coordinates of the center point and name(cx, cy,name).
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
    Flip Y coordinates to convert from PyMuPDF coordinate system to standard plotting coordinates.
    
    PyMuPDF: (0,0) at top-left, Y increases downward
    Standard: (0,0) at bottom-left, Y increases upward
    
    Args:
        centerpoints: List of [cx, cy, name] coordinates from PyMuPDF
        page_height: Height of the PDF page (page.rect.height)
    
    Returns:
        List of [cx, cy_flipped, name] with flipped Y coordinates
    """
    flipped_centerpoints = []
    
    for point in centerpoints:
        cx, cy, name = point[0], point[1], point[2]
        cy_flipped = page_height - cy  # Flip Y coordinate
        flipped_centerpoints.append([cx, cy_flipped, name])
    
    return flipped_centerpoints


def extract_voronoi_neighbors(centerpoints):
    """
    Extract only neighbor relationships from Voronoi diagram.
    
    Args:
        centerpoints: List of [cx, cy, name] coordinates
    
    Returns:
        dict: Dictionary with room names as keys and lists of neighbors as values
    """
    if len(centerpoints) < 3:
        raise ValueError("Need at least 3 points for Voronoi diagram")
    
    # Extract coordinates and names
    points = np.array([[cp[0], cp[1]] for cp in centerpoints])
    names = [cp[2] for cp in centerpoints]
    
    # Create Voronoi diagram
    vor = Voronoi(points)
    
    # Find neighbors
    neighbors_dict = defaultdict(set)
    
    # Process ridge information (connections between regions)
    for ridge in vor.ridge_points:
        point1_idx, point2_idx = ridge
        name1 = names[point1_idx]
        name2 = names[point2_idx]
        
        # Add to neighbors
        neighbors_dict[name1].add(name2)
        neighbors_dict[name2].add(name1)
    
    # Convert to regular dict with sorted lists
    neighbors = {name: sorted(list(neighbors)) for name, neighbors in neighbors_dict.items()}
    
    return neighbors, vor

def visualize_voronoi_cells(vor, centerpoints, neighbors, save_path=None):
    """
    Simple visualization of Voronoi cells with room labels.
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Plot Voronoi diagram
    voronoi_plot_2d(vor, ax=ax, show_vertices=False, line_colors='blue', line_width=2)
    
    # Plot center points and labels
    for i, cp in enumerate(centerpoints):
        ax.plot(cp[0], cp[1], 'ro', markersize=8)
        ax.text(cp[0], cp[1], cp[2], fontsize=10, ha='center', va='bottom', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    ax.set_title('Voronoi Diagram - Room Adjacencies', fontsize=14)
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.grid(True, alpha=0.3)
    
    # Add neighbor count in title
    total_connections = sum(len(neighs) for neighs in neighbors.values()) // 2
    ax.text(0.02, 0.98, f'Total room connections: {total_connections}', 
            transform=ax.transAxes, fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()

def print_neighbors_summary(neighbors):
    """
    Print a clean summary of neighbors.
    """
    print("\n=== ROOM NEIGHBORS ===")
    for room, room_neighbors in neighbors.items():
        print(f"{room}: {', '.join(room_neighbors)}")

def save_neighbors_only(neighbors, filename="room_neighbors.json"):
    """
    Save only the neighbor information to JSON.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(neighbors, f, indent=2, ensure_ascii=False)
    print(f"Neighbors saved to '{filename}'")

def analyze_room_connectivity(neighbors):
    """
    Simple analysis of room connectivity.
    """
    print("\n=== CONNECTIVITY ANALYSIS ===")
    
    # Count connections
    connection_counts = {room: len(neighs) for room, neighs in neighbors.items()}
    
    # Most connected room
    most_connected = max(connection_counts, key=connection_counts.get)
    print(f"Most connected room: {most_connected} ({connection_counts[most_connected]} connections)")
    
    # Least connected room
    least_connected = min(connection_counts, key=connection_counts.get)
    print(f"Least connected room: {least_connected} ({connection_counts[least_connected]} connections)")
    
    # Average connections
    avg_connections = sum(connection_counts.values()) / len(connection_counts)
    print(f"Average connections per room: {avg_connections:.1f}")
    
    # Sort rooms by connectivity
    sorted_rooms = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)
    print(f"\nRooms by connectivity:")
    for room, count in sorted_rooms:
        print(f"  {room}: {count} connections")

def process_simple_voronoi(centerpoints, filename, bounds=None):
    """
    Complete simple workflow for neighbor extraction and visualization.
    """
    try:
        print(f"Processing {len(centerpoints)} rooms...")
        
        # Extract neighbors
        neighbors, vor = extract_voronoi_neighbors(centerpoints)
        
        # Save neighbors
        save_neighbors_only(neighbors,filename)
        
        # Print summary
        print_neighbors_summary(neighbors)
        
        # Analyze connectivity
        analyze_room_connectivity(neighbors)
        
        # Visualize
        visualize_voronoi_cells(vor, centerpoints, neighbors, "voronoi_cells.png")
        
        return neighbors, vor
        
    except Exception as e:
        print(f"Error processing Voronoi: {e}")
        return None, None

def get_room_neighbors(neighbors, room_name):
    """
    Get neighbors of a specific room.
    """
    return neighbors.get(room_name, [])

def find_path_between_rooms(neighbors, start_room, end_room):
    """
    Find if there's a direct connection or path between two rooms.
    """
    if start_room not in neighbors or end_room not in neighbors:
        return None
    
    if end_room in neighbors[start_room]:
        return [start_room, end_room]  # Direct connection
    
    # Simple breadth-first search for shortest path
    from collections import deque
    
    queue = deque([(start_room, [start_room])])
    visited = {start_room}
    
    while queue:
        current_room, path = queue.popleft()
        
        for neighbor in neighbors[current_room]:
            if neighbor == end_room:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None  # No path found



if __name__=="__main__":
    #pdf_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf.pdf"
    #pdf_path= "examples/FloorplansAndSectionViews/BasicTestPlan.pdf"
    pdf_path = "examples/FloorplansAndSectionViews/eg-musterplan-1-50_2023 (1).pdf"

    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    json_path = f'output/Floorplan/Neighbouring rooms/{filename}_neighbouring_rooms.json'

    
    doc = fitz.open(pdf_path)

    page = doc[0]
    # clip rectangle to exclude plan information -> using fitz.Rect(x0, y0, x1, y1) where x0,yo is top left corner and x1,y1 is bottom right corner
    width,height = page.rect.width, page.rect.height
    clip_rect = fitz.Rect(0, 0, width * 0.8, height * 0.8)
    page.add_rect_annot(clip_rect)

    # Save to a debug file
    doc.save("clipped_debug.pdf")

    word = page.get_textpage(clip_rect)
    bbox = word.extractWORDS() # returns a list [x0, y0, x1, y1, "text", block_no, line_no, word_no]

    # WORKING WITH WORD EXTRACTION
    filtered_bbox_number = [entry for entry in bbox if not is_number_like(entry[4])]
    filtered_bbox_string = [entry for entry in filtered_bbox_number if has_more_than_one_char(entry[4])]
    combined_bbox = combine_close_words(filtered_bbox_string)

    for entry in filtered_bbox_string:
        x0, y0, x1, y1 = entry[0], entry[1], entry[2], entry[3]
        rect= fitz.Rect(x0, y0, x1, y1)
        page.add_rect_annot(rect)
        
    doc.save("clipped_debug_filltered.pdf")

    output_filename= "textbboxes_rooms"
    with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(combined_bbox,f, indent=2, ensure_ascii=False)
                print(f"Successfully saved extracted JSON to '{output_filename}'")

    # calculate the centerpoints of the room 
    centerpoints = []
    for entry in combined_bbox:
        centerpoint = calculate_bbox_center(entry)
        centerpoints.append(centerpoint)
    
    output_filename= "centerpoints_rooms"
    with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(centerpoints,f, indent=2, ensure_ascii=False)
                print(f"Successfully saved extracted JSON to '{output_filename}'")
    # create voronoi polygons around the center points 
    page_width, page_height = page.rect.width, page.rect.height
    flipped_centerpoints = flip_y_coordinates(centerpoints,page_height)
    voronoi_polygons =process_simple_voronoi(flipped_centerpoints,json_path)

