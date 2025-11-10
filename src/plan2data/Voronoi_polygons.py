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
    text = re.sub(r"(m²|m|cm|°|%|\s+|ca|ca.|m2| qm | og| eg| ug| nr| nr.)", "", text, flags=re.IGNORECASE)
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

def is_valid_room_name(text):
    """
    Room names should be at least one meaningful word.
    """
    text = text.strip()
    
    # Minimum length
    if len(text) < 3:
        return False
    
    # Common abbreviations to exclude
    excluded = {'ca', 'ca.', 'cm', 'm²', 'm2', 'qm', 'og', 'eg', 'ug', 'nr', 'nr.', 'wc'}
    if text.lower() in excluded:
        return False
    
    # Must contain at least one letter (not just numbers/symbols)
    if not any(c.isalpha() for c in text):
        return False
    
    # Optional: Must have at least 3 letters total
    letter_count = sum(1 for c in text if c.isalpha())
    if letter_count < 3:
        return False
    
    return True
    

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

def save_neighbors_only(neighbors, filename):
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



def extract_bounded_voronoi_neighbors_detailed(centerpoints, bounds):
    """
    Detailed version that prints why each ridge is accepted/rejected.
      Args:
        centerpoints of bboxes of identified textboxes which qualify as room names
        bounds of the floorplan
    
    Returns:
        neighbors: list of neighbours 
        voronoi cells of rooms         

    """
    if len(centerpoints) < 3:
        raise ValueError("Need at least 3 points for Voronoi diagram")
    
    points = np.array([[cp[0], cp[1]] for cp in centerpoints])
    names = [cp[2] for cp in centerpoints]
    
    print(f"\n=== ROOM POSITIONS ===")
    for i, (cp, name) in enumerate(zip(centerpoints, names)):
        print(f"{name}: ({cp[0]:.1f}, {cp[1]:.1f})")
    
    vor = Voronoi(points)
    
    x_min, y_min, x_max, y_max = bounds
    #print(f"\n=== BOUNDS ===")
    #print(f"X: {x_min:.1f} to {x_max:.1f}")
    #print(f"Y: {y_min:.1f} to {y_max:.1f}")
    
    neighbors_dict = defaultdict(set)
    
    print(f"\n=== PROCESSING RIDGES ===")
    for ridge_idx, ridge_points in enumerate(vor.ridge_points):
        point1_idx, point2_idx = ridge_points
        name1 = names[point1_idx]
        name2 = names[point2_idx]
        
        ridge_vertices = vor.ridge_vertices[ridge_idx]
        
        #print(f"\n{ridge_idx}. {name1} <-> {name2}")
        
        if -1 in ridge_vertices:
            #print(f"   Type: INFINITE ridge")
            # Get finite vertex
            finite_idx = ridge_vertices[0] if ridge_vertices[1] == -1 else ridge_vertices[1]
            if finite_idx >= 0:
                finite_v = vor.vertices[finite_idx]
                #print(f"   Finite vertex: ({finite_v[0]:.1f}, {finite_v[1]:.1f})")
                
                # Check if finite vertex is in bounds
                v_in = x_min <= finite_v[0] <= x_max and y_min <= finite_v[1] <= y_max
                #print(f"   Vertex in bounds: {v_in}")
                
                if v_in:
                    neighbors_dict[name1].add(name2)
                    neighbors_dict[name2].add(name1)
                    print(f"   ✓ ADDED")
                else:
                    print(f"   ✗ REJECTED (vertex outside bounds)")
        else:
           # print(f"   Type: FINITE ridge")
            v1 = vor.vertices[ridge_vertices[0]]
            v2 = vor.vertices[ridge_vertices[1]]
            
            #print(f"   Vertex 1: ({v1[0]:.1f}, {v1[1]:.1f})")
            #print(f"   Vertex 2: ({v2[0]:.1f}, {v2[1]:.1f})")
            
            v1_in = x_min <= v1[0] <= x_max and y_min <= v1[1] <= y_max
            v2_in = x_min <= v2[0] <= x_max and y_min <= v2[1] <= y_max
            
            midpoint_x = (v1[0] + v2[0]) / 2
            midpoint_y = (v1[1] + v2[1]) / 2
            mid_in = x_min <= midpoint_x <= x_max and y_min <= midpoint_y <= y_max
            
            #print(f"   V1 in bounds: {v1_in}, V2 in bounds: {v2_in}")
            #print(f"   Midpoint: ({midpoint_x:.1f}, {midpoint_y:.1f}), in bounds: {mid_in}")
            
            # Accept if midpoint is in bounds OR if any vertex is in bounds
            if mid_in or v1_in or v2_in:
                neighbors_dict[name1].add(name2)
                neighbors_dict[name2].add(name1)
                print(f"   ✓ ADDED")
            else:
                print(f"   ✗ REJECTED (all points outside bounds)")
    
    neighbors = {name: sorted(list(neighs)) for name, neighs in neighbors_dict.items()} 
    return neighbors, vor


def process_simple_voronoi(centerpoints, filename, bounds):
    """
    Complete simple workflow for neighbor extraction and visualization.
    """
    try:
        print(f"Processing {len(centerpoints)} rooms...")
        
        # Extract neighbors
        #neighbors, vor = extract_voronoi_neighbors(centerpoints)
        neighbors, vor = extract_bounded_voronoi_neighbors_detailed(centerpoints, bounds)
        
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

if __name__=="__main__":
    # Change to the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    os.chdir(project_root)
    #pdf_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf.pdf"
    #pdf_path= "examples/FloorplansAndSectionViews/BasicTestPlan.pdf"
    #pdf_path = "examples/FloorplansAndSectionViews/GrundrissEG_2022_web.pdf"
    pdf_path = "examples/FloorplansAndSectionViews/2d-grundriss-wohnflaeche.pdf"

    # NAMING convention of output files 
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    json_path = f'output/Floorplan/Neighbouring rooms/{filename}_neighbouring_rooms.json'
    output_filename= f'output/Floorplan/Neighbouring rooms/{filename}_textbboxes_rooms.json'
    output_PDF = f'output/Floorplan/Neighbouring rooms/{filename}_clipped_debug_filltered.pdf'
    
    doc = fitz.open(pdf_path)

    page = doc[0]
    # clip rectangle to exclude plan information -> using fitz.Rect(x0, y0, x1, y1) where x0,yo is top left corner and x1,y1 is bottom right corner
    width,height = page.rect.width, page.rect.height
    clip_rect = fitz.Rect(0, 0, width * 0.72, height * 0.8)
    flipped_rect =(
        clip_rect.x0,                    # x_min stays the same
        height - clip_rect.y1,           # y_min (flip the bottom of clip_rect)
        clip_rect.x1,                    # x_max stays the same
        height - clip_rect.y0            # y_max (flip the top of clip_rect)
    )
    page.add_rect_annot(clip_rect)

    # Save to a debug file
    doc.save("clipped_debug.pdf")

    word = page.get_textpage(clip_rect)
    bbox = word.extractWORDS() # returns a list [x0, y0, x1, y1, "text", block_no, line_no, word_no]

    # WORKING WITH WORD EXTRACTION
    filtered_bbox_number = [entry for entry in bbox if not is_number_like(entry[4])]
    filtered_bbox_string_1 = [entry for entry in filtered_bbox_number if is_valid_room_name(entry[4])]
    filtered_bbox_string = [entry for entry in filtered_bbox_string_1 if has_more_than_one_char(entry[4])]
    combined_bbox = combine_close_words(filtered_bbox_string)

    for entry in combined_bbox:
        x0, y0, x1, y1 = entry[0], entry[1], entry[2], entry[3]
        rect= fitz.Rect(x0, y0, x1, y1)
        page.add_rect_annot(rect)
        
    doc.save(output_PDF)


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
    #voronoi_polygons = extract_bounded_voronoi_neighbors_detailed(flipped_centerpoints, flipped_rect)
    voronoi_polygons =process_simple_voronoi(flipped_centerpoints,json_path, flipped_rect)

