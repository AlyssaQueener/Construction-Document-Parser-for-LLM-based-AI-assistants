import fitz
import json
import re 
from scipy.spatial import Voronoi
import numpy as np
from collections import defaultdict
import src.plan2data.mistralConnection as mistral
import base64
import pymupdf
import src.plan2data.titleBlockInfo as tb


def convert_pdf_to_base64(pdf_path: str, page: int = 0):
    """Convert specific PDF page to base64 encoded image string"""
    # Open the document
    pdfIn = pymupdf.open(pdf_path)
    
    # Select the page
    page_obj = pdfIn[page]
    
    # Convert to image
    pix = page_obj.get_pixmap(dpi=300)
    
    # Save to bytes
    img_bytes = pix.pil_tobytes(format="PNG")
    
    # Encode to base64
    base64_image = base64.b64encode(img_bytes).decode('utf-8')
    
    pdfIn.close()
    
    return base64_image


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
    if s.upper() == 'WC':
        return True
    return len(s) > 2








    
    



def extract_text_from_pdf(pdf_path, clean=True):
    """
    Extract all text from PDF and optionally clean it.
    
    Args:
        pdf_path (str): Path to the input PDF file
        clean (bool): If True, filter out numbers, coordinates, and short strings
        
    Returns:
        str: All extracted text concatenated
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
                            # Filter anwenden
                            if is_number_like(text) or is_number_block(text):
                                filtered_count += 1
                                continue
                            
                            if not has_more_than_one_char(text):
                                filtered_count += 1
                                continue
                        
                        all_text.append(text)
    
    doc.close()
    
    # Debug-Info ausgeben
    if clean:
        print(f"📊 Text Extraktion Statistik:")
        print(f"   Gesamt gefunden: {total_count}")
        print(f"   Herausgefiltert: {filtered_count}")
        print(f"   An AI gesendet: {len(all_text)}")
        print(f"   Filterrate: {(filtered_count/total_count*100):.1f}%\n")
    
    # Alle Texte mit Leerzeichen verbinden
    return " ".join(all_text)



def ai_roomnames_from_pdf(pdf_path):
    """
    Extract room names from PDF using AI.
    """
    # Text extrahieren und bereinigen
    text = extract_text_from_pdf(pdf_path, clean=True)
    
    # Validierung
    if not text or text.strip() == "":
        print("⚠️  Warning: No text extracted from PDF after filtering")
        return []
    
    print(f"📝 Sende {len(text)} Zeichen an Mistral AI...")
    print(f"📄 Erste 500 Zeichen des Textes:")
    print("-" * 80)
    print(text[:500])
    print("-" * 80)
    print()
    
    # An AI senden
    room_names_ai = mistral.call_mistral_roomnames(text)
    
    print(f"🤖 AI Antwort: {room_names_ai}")
    print(f"📊 Anzahl gefundener Räume: {len(room_names_ai)}")
    
    return room_names_ai



def is_valid_room_name(text, room_names_ai):
    """
    Determines if the provided text qualifies as a valid room name.
    
    Args:
        text (str): The text candidate for a room name.
        room_names_ai (list): List of room names identified by AI.
        
    Returns:
        bool: True if considered a valid room name, False otherwise.
    """
    expanded_names = []
    for name in room_names_ai:
        # Add the original name
        expanded_names.append(name)
        # Add split components if there are spaces
        # Add split components if there are spaces
        if ' ' in name:
            components = name.split()
            for comp in components:
                # Add the component as-is
                expanded_names.append(comp)
               
    
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip()
    
    # Leere Strings ablehnen
    if not text:
        return False
    
    # Spezialfall: WC ist immer gültig
    if text.upper() == 'WC':
        return True
    
    # 1. Check: Ist der Text in der AI-Liste?
    if expanded_names:
        included = {name.lower().strip() for name in expanded_names}
        if text.lower() in included:
            return True
    # Mindestlänge: 3 Zeichen (außer WC)
    if len(text) < 3:
        return False
    # 2. Explizite Ausschlussliste (erweitert)
    excluded = {
        # Einheiten und Maße
        'ca', 'ca.', 'cm', 'm²', 'm2', 'qm', 'mm', 'dm', 
        # Geschosse
        'og', 'eg', 'ug', 'dg', 'kg', '1.og', '2.og', 'brh'
        #Hinweise und Zusatzinformationen
        'nts','abb.', 'abb','allg', 'allg.', 'bes.', 'bes', 'bez.', 'bez', 'bezg', 'Bez', 'Bez.'
        # Nummern und Referenzen
        'nr', 'nr.', 'no', 'no.', 'pos', 'pos.',
        # Plan-Begriffe
        'plan', 'detail', 'schnitt', 'ansicht', 'grundriss','fläche', 'maßstab','massstab', 'zimmertüren', 'türen'
        # Maßstäbe
        '1:50', '1:100', '1:200', '1:500',
        # Technische Abkürzungen
        'dn', 'nw', 'dia', 'durchm.', 
        # Administrative Begriffe
        'datum', 'gepr', 'gez', 'bearb', 'index',
        # Himmelsrichtungen
        'nord', 'süd', 'ost', 'west', 'n', 's', 'o', 'w',
        # Achsbezeichnungen (Zahlen werden woanders gefiltert)
        'achse', 'raster',
    }
    
    if text.lower() in excluded:
        return False
    
    # 3. Zahlen-Pattern ablehnen (reine Zahlen oder Koordinaten)
    # Erlaubt: "Raum 1.01", "Zimmer 2"
    # Ablehnt: "1.50", "12.5", "2.40"
    # if re.match(r'^[\d.,]+', text):
    #     return False
    
    # # 4. Technische Codes ablehnen (z.B. "DN 100", "Ø 50")
    # if re.match(r'^[A-Z]{1,3}\s*\d+', text, re.IGNORECASE):
    #     # Ausnahme: Zimmernummern wie "Z1", "R2.1" sind OK
    #     if not re.match(r'^[ZR]\d', text, re.IGNORECASE):
    #         return False
    
    # 5. Wenn AI eine Liste zurückgegeben hat, nur diese akzeptieren
    #(Strenge Filterung)
    if expanded_names:
        return False  # Nicht in AI-Liste, also ablehnen
    
    # 6. Fallback: Wenn AI keine Liste hat, verwende Heuristiken
    # Typische Raum-Keywords
    room_keywords = [
        'zimmer', 'raum', 'bad', 'wc', 'küche', 'keller', 'diele', 'flur',
        'wohn', 'schlaf', 'kind', 'gäste', 'arbeits', 'büro', 'ess',
        'abstell', 'hauswirtschaft', 'hwr', 'technik', 'heizung',
        'garage', 'carport', 'terrasse', 'balkon', 'loggia',
        'eingang', 'windfang', 'vorraum', 'ankleide', 'schrank',
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in room_keywords)
    

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


def make_names_unique(centerpoints):
    """
    Makes duplicate room names unique by adding sequential numbers.
    
    Args:
        centerpoints (list of list): [cx, cy, name] for all rooms.
        
    Returns:
        list of list: Modified centerpoints with unique names.
    """
    name_counts = {}
    unique_centerpoints = []
    centerpoints = sorted(centerpoints, key=lambda cp: cp[0])  # Sort by x (cx)
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
    Adds positional indices to neighbor relationships for duplicate room names.
    
    Args:
        neighbors (dict): room name to list of neighbor names
        centerpoints (list of list): [cx, cy, name] for all rooms
        
    Returns:
        dict: Enhanced neighbor data with indices for duplicate names
    """
    # Sort centerpoints left to right
    sorted_cp = sorted(enumerate(centerpoints), key=lambda x: x[1][0])  # Sort by x-coordinate
    
    # Map original indices to their left-to-right position for each room name
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
        # Get all instances of this room name
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
                    'neighbors': neighs  # You might need to update this based on which specific instance
                }
    
    return enhanced_neighbors


def neighboring_rooms_voronoi(pdf_path):
    """
    Extract neighboring rooms from a floorplan PDF using Voronoi diagram.
    
    Args:
        pdf_path: Path to the PDF file to process
        
    Returns:
        dict: Dictionary mapping room names to their list of neighboring rooms
    """
    room_names_ai = ai_roomnames_from_pdf(pdf_path)
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Clip rectangle to exclude plan information
    width, height = page.rect.width, page.rect.height
    clip_rect = fitz.Rect(0, 0, width * 0.7, height * 0.8)
    flipped_rect = (
        clip_rect.x0,
        height - clip_rect.y1,
        clip_rect.x1,
        height - clip_rect.y0
    )
    
    # Extract and filter words
    word = page.get_textpage(clip_rect)
    bbox = word.extractWORDS()
    
    
    #
    filtered_bbox_string_1 = [entry for entry in bbox if is_valid_room_name(entry[4],room_names_ai)]
    #
    combined_bbox = combine_close_words(filtered_bbox_string_1)
    filtered_bbox_number = [entry for entry in combined_bbox if not is_number_like(entry[4])]
    filtered_bbox_string = [entry for entry in filtered_bbox_number if has_more_than_one_char(entry[4])]
    # Calculate centerpoints
    centerpoints = []
    for entry in filtered_bbox_string:
        centerpoint = calculate_bbox_center(entry)
        centerpoints.append(centerpoint)
    
    # Create voronoi polygons around the center points
    page_width, page_height = page.rect.width, page.rect.height
    flipped_centerpoints = flip_y_coordinates(centerpoints, page_height)
    flipped_centerpoints = make_names_unique(flipped_centerpoints)
    neighbors, vor = extract_bounded_voronoi_neighbors_detailed(flipped_centerpoints, flipped_rect)
    doc.close()
    
    # Print as JSON and return
    return neighbors


def extract_full_floorplan(pdf_path):
    """
    Extract connected rooms from a floorplan PDF using Voronoi diagram and Mistral AI.
    
    Args:
        pdf_path: Path to the PDF file to process
    Returns:
        str: JSON string with titleblock, neighboring rooms, and connected rooms
    """
    try:
        # 1. Get neighboring rooms from Voronoi analysis
        neighbors_vor = neighboring_rooms_voronoi(pdf_path)
        
        # 2. Convert to dict if it's a JSON string
        if isinstance(neighbors_vor, str):
            neighbors_vor = json.loads(neighbors_vor)
        
        # 3. Convert PDF to base64 image
        base64_image = convert_pdf_to_base64(pdf_path)
        
        #titleblock, method, is_succesful, confidence = tb.get_title_block_info(pdf_path)
        
        # 4. Call Mistral to identify actual connections
        connected_rooms_response = mistral.call_mistral_connected_rooms(base64_image, json.dumps(neighbors_vor))
        
        # 5. Parse response if it's a string
        if isinstance(connected_rooms_response, str):
            connected_rooms = json.loads(connected_rooms_response)
        else:
            connected_rooms = connected_rooms_response
        
        # 6. Combine all outputs (als dict, nicht string!)
        full_floorplan = {
            #"titleblock": titleblock,
            "neighboring_rooms": neighbors_vor,  
            "connected_rooms": connected_rooms
        }
        
        # 7. Schön formatiert ausgeben
        formatted_output = json.dumps(full_floorplan, indent=2, ensure_ascii=False)
        print("\n📋 Full Floorplan Data:")
        print(formatted_output)
        
        return formatted_output
        
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {e}")
        return "{}"
    
if __name__ == "__main__":
    #pdf_path = "src/validation/Floorplan/titleblock/testdata/floorplan-test-2.pdf" 
    pdf_path = "src/validation/Floorplan/neighboring rooms/Simple Floorplan/Simple Floorplan/01_Simple.pdf" 
    #pdf_path = "examples/FloorplansAndSectionViews/Simple Floorplan/02_Simple.pdf"
    #pdf_path ="src/validation/Floorplan/titleblock/testdata/floorplan-test-1.pdf"
    #neighbors_json = neighboring_rooms_voronoi(pdf_path)
    #print(neighbors_json)
    connected_rooms = extract_full_floorplan(pdf_path)
    print(connected_rooms)