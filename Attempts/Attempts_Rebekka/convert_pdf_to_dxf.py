
from ezdxf.math import Vec2
import fitz  # PyMuPDF
import ezdxf #https://ezdxf.readthedocs.io/en/stable/concepts/coordinates.html#wcs
from collections import defaultdict
from collections import Counter




def convert_PDF_to_cm_point( PDF_x, PDF_y,PDF_scale=1):
    """
    Convert PDF coordinate points to centimeters.
    
    Args:
        PDF_scale (float): Scaling factor for the conversion
        PDF_x (float): X coordinate in PDF units
        PDF_y (float): Y coordinate in PDF units
    
    Returns:
        tuple: (CM_x, CM_y) coordinates in centimeters
    
    Note:
        PDF uses 72 units per inch, and 1 inch = 2.54 cm
    """
    PDF_Unit_to_cm = 2.54 / 72  # 72 PDF units = 1 inch = 2.54 cm
    CM_x = PDF_x * PDF_Unit_to_cm * PDF_scale
    CM_y = PDF_y * PDF_Unit_to_cm * PDF_scale
    Pt_cm = (CM_x, CM_y)
    return Pt_cm


def convert_PDF_to_cm(PDF_cord,PDF_scale=1):
    """
    Convert a single PDF coordinate value to centimeters.
    
    Args:
        PDF_scale (float): Scaling factor for the conversion
        PDF_cord (float): Coordinate value in PDF units
    
    Returns:
        float: Coordinate value in centimeters
    """
    PDF_Unit_to_cm = 2.54 / 72  # 72 PDF units = 1 inch = 2.54 cm
    CM_cord = PDF_cord * PDF_Unit_to_cm * PDF_scale
    return CM_cord


def create_dxf_document_with_layers():
    """
    Create a new DXF document with predefined layers for different geometry types.
    
    Returns:
        tuple: (dxf_doc, msp) where:
               - dxf_doc: ezdxf.Drawing object
               - msp: Modelspace object for adding entities
    
    Layers created:
        - PDFLines: Straight line segments
        - PDFRects: Rectangles and filled shapes
        - PDFSplines: Spline curves
        - PDFCurves: Ellipses and circles
        - PDFText: Text annotations
        - PDFFilledshapes: Filled polygons
        - PDFQuads: Quadrilaterals
    """
    dxf_doc = ezdxf.new()
    
    # Define layers for different geometric primitives
    dxf_doc.layers.new('PDFLines')
    dxf_doc.layers.new('PDFRects')
    dxf_doc.layers.new('PDFSplines')
    dxf_doc.layers.new('PDFCurves')
    dxf_doc.layers.new('PDFText')
    dxf_doc.layers.new('PDFFilledshapes')
    dxf_doc.layers.new('PDFQuads')
    
    msp = dxf_doc.modelspace()
    
    return dxf_doc, msp


def analyze_drawing_elements(drawings):
    """
    Analyze and count the types of drawing elements in a page.
    
    Args:
        drawings (list): List of drawing elements from PyMuPDF
    
    Returns:
        Counter: Dictionary mapping shape type codes to their counts
    
    Shape type codes:
        'l': Line
        're': Rectangle
        'c': Cubic Bezier curve
        'el': Ellipse/Circle
        'f': Filled path
        'qu': Quadrilateral
    """
    type_counter = Counter()
    
    for item in drawings:
        for element in item["items"]:
            if isinstance(element, (list, tuple)) and len(element) > 0:
                shape_type = element[0]
                type_counter[shape_type] += 1
    
    return type_counter


def convert_line_to_dxf(element, page_height, msp):
    """
    Convert a PDF line segment to DXF format.
    
    Args:
        element (tuple): Line element in format ("l", point1, point2)
        page_height (float): Height of the PDF page for Y-coordinate conversion
        msp: DXF modelspace object
    
    Returns:
        tuple: (pt1, pt2) converted line endpoints, or None if invalid
    """
    if element[0] != "l" or len(element) != 3:
        return None
    
    _, p1, p2 = element
    # Convert Y coordinates (flip vertical axis)
    pt1 = (round(p1.x, 2), round(page_height - p1.y, 2))
    pt2 = (round(p2.x, 2), round(page_height - p2.y, 2))
    
    # Add line to DXF modelspace
    msp.add_line(pt1, pt2, dxfattribs={"layer": "PDFLines"})
    
    return (pt1, pt2)


def convert_rectangle_to_dxf(element, page_height, msp):
    """
    Convert a PDF rectangle to DXF format.
    
    Args:
        element (tuple): Rectangle element in format ("re", rect, fill)
        page_height (float): Height of the PDF page for Y-coordinate conversion
        msp: DXF modelspace object
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    if element[0] != "re" or len(element) != 3:
        return False
    
    _, rect, fill = element
    # Convert rectangle corners
    x0, y0 = rect.x0, page_height - rect.y0
    x1, y1 = rect.x1, page_height - rect.y1
    
    # Add filled rectangle as solid
    msp.add_solid(
        [(x0, y0), (x1, y0), (x0, y1), (x1, y1)],
        dxfattribs={"layer": "PDFRects"}
    )
    
    return True


def convert_bezier_curve_to_dxf(element, page_height, msp):
    """
    Convert a PDF cubic Bezier curve to DXF spline.
    
    Args:
        element (tuple): Curve element in format ("c", start, cp1, cp2, end)
        page_height (float): Height of the PDF page for Y-coordinate conversion
        msp: DXF modelspace object
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    if element[0] != "c" or len(element) != 5:
        return False
    
    _, start, cp1, cp2, end = element
    
    # Convert all control points Y coordinates
    control_points = [
        (start[0], page_height - start[1]),
        (cp1[0], page_height - cp1[1]),
        (cp2[0], page_height - cp2[1]),
        (end[0], page_height - end[1])
    ]
    
    # Create cubic spline (degree 3 Bezier curve)
    msp.add_spline(
        control_points,
        degree=3,
        dxfattribs={"layer": "PDFCurves"}
    )
    
    return True


def convert_ellipse_to_dxf(element, page_height, msp):
    """
    Convert a PDF ellipse or circle to DXF format.
    
    Args:
        element (tuple): Ellipse element in format ("el", ellipse_obj)
        page_height (float): Height of the PDF page for Y-coordinate conversion
        msp: DXF modelspace object
    
    Returns:
        bool: True if conversion successful, False otherwise
    
    Note:
        Automatically detects circles (equal radii) and uses appropriate DXF entity
    """
    if element[0] != "el" or len(element) != 2:
        return False
    
    _, ellipse = element
    cx, cy = ellipse.center
    rx, ry = ellipse.rx, ellipse.ry  # X and Y radii
    rotation = ellipse.rotation
    
    # Check if it's actually a circle (equal radii)
    if abs(rx - ry) < 1e-3:
        msp.add_circle(
            center=(cx, page_height - cy),
            radius=rx,
            dxfattribs={"layer": "PDFCurves"}
        )
    else:
        # True ellipse
        msp.add_ellipse(
            center=(cx, page_height - cy),
            major_axis=(rx, 0),
            ratio=ry / rx,
            dxfattribs={"layer": "PDFCurves"}
        )
    
    return True


def convert_filled_path_to_dxf(element, page_height, msp):
    """
    Convert a PDF filled path to DXF closed polyline.
    
    Args:
        element (tuple): Filled path element in format ("f", [points])
        page_height (float): Height of the PDF page for Y-coordinate conversion
        msp: DXF modelspace object
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    if element[0] != 'f' or not isinstance(element[1], list):
        return False
    
    filled_path = element[1]
    if len(filled_path) < 3:
        return False
    
    # Convert all points
    points = [(pt.x, page_height - pt.y) for pt in filled_path]
    
    # Add as closed polyline (lightweight polyline)
    msp.add_lwpolyline(
        points,
        dxfattribs={"layer": "PDFFilledshapes"},
        close=True
    )
    
    return True


def convert_quad_to_dxf(element, page_height, msp):
    """
    Convert a PDF quadrilateral to DXF polyline.
    
    Args:
        element (tuple): Quad element in format ("qu", quad_obj)
        page_height (float): Height of the PDF page for Y-coordinate conversion
        msp: DXF modelspace object
    
    Returns:
        bool: True if conversion successful, False otherwise
    
    Note:
        Quad structure: TopLeft, BottomLeft, TopRight, BottomRight
    """
    if element[0] != 'qu' or len(element) != 2:
        return False
    
    _, quad = element
    p0, p1, p2, p3 = quad
    
    # Close the polyline by repeating first point
    points = [
        (p0.x, page_height - p0.y),
        (p1.x, page_height - p1.y),
        (p3.x, page_height - p3.y),
        (p2.x, page_height - p2.y),
        (p0.x, page_height - p0.y),  # Close path
    ]
    
    msp.add_lwpolyline(points, dxfattribs={"layer": "PDFQuads"})
    
    return True


def convert_geometry_elements(drawings, page_height, msp):
    """
    Convert all geometry elements from PDF page to DXF entities.
    
    Args:
        drawings (list): List of drawing elements from PyMuPDF
        page_height (float): Height of the PDF page for Y-coordinate conversion
        msp: DXF modelspace object
    
    Returns:
        dict: Statistics about converted elements
              Keys: 'lines', 'rectangles', 'curves', 'ellipses', 'filled_paths', 'quads'
    """
    stats = {
        'lines': 0,
        'rectangles': 0,
        'curves': 0,
        'ellipses': 0,
        'filled_paths': 0,
        'quads': 0
    }
    
    for item in drawings:
        for element in item["items"]:
            # Skip non-tuple/list elements
            if not isinstance(element, (list, tuple)):
                continue
            
            # Convert based on element type
            if convert_line_to_dxf(element, page_height, msp):
                stats['lines'] += 1
            elif convert_rectangle_to_dxf(element, page_height, msp):
                stats['rectangles'] += 1
            elif convert_bezier_curve_to_dxf(element, page_height, msp):
                stats['curves'] += 1
            elif convert_ellipse_to_dxf(element, page_height, msp):
                stats['ellipses'] += 1
            elif convert_filled_path_to_dxf(element, page_height, msp):
                stats['filled_paths'] += 1
            elif convert_quad_to_dxf(element, page_height, msp):
                stats['quads'] += 1
    
    return stats


def extract_and_convert_text(page, page_height, msp):
    """
    Extract text from PDF page and add to DXF as text entities.
    
    Args:
        page: PyMuPDF page object
        page_height (float): Height of the PDF page for Y-coordinate conversion
        msp: DXF modelspace object
    
    Returns:
        int: Number of text entities created
    """
    text_count = 0
    
    # Extract text with positioning information
    textpage = page.get_textpage()
    text_dict = textpage.extractDICT()
    
    for block in text_dict["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    x, y = span["origin"]  # Text insertion point
                    text = span["text"]    # Text content
                    font_height = span["size"]  # Font size
                    
                    # Convert Y coordinate to DXF coordinate system
                    dxf_y = page_height - y
                    
                    # Create text entity
                    text_entity = msp.add_text(
                        text,
                        dxfattribs={
                            "height": font_height,
                            "layer": "PDFText"
                        }
                    )
                    # Set text insertion point
                    text_entity.dxf.insert = (x, dxf_y)
                    text_count += 1
    
    return text_count


def print_dxf_statistics(dxf_doc, msp):
    """
    Print statistics about the DXF document layers and entities.
    
    Args:
        dxf_doc: ezdxf.Drawing object
        msp: DXF modelspace object
    """
    # Print all layers
    print("\n📋 Layers in DXF document:")
    for layer in dxf_doc.layers:
        print(f"Layer: {layer.dxf.name}")
    
    # Count entities per layer
    layer_counts = Counter()
    for entity in msp:
        layer_counts[entity.dxf.layer] += 1
    
    # Print entity distribution
    print("\n📊 Entity count per layer:")
    for layer, count in layer_counts.items():
        print(f"  - {layer}: {count} entities")
    
    print(f"\n✅ Total entities in modelspace: {len(msp)}")


def convert_pdf_to_dxf(pdf_path, output_path="converted_output_with_text_and_curves.dxf"):
    """
    Convert a PDF floor plan to DXF format, preserving all geometry and text.
    
    This function orchestrates the complete conversion pipeline:
    1. Opens PDF document
    2. Creates DXF document with layers
    3. Extracts and converts geometry from each page
    4. Extracts and converts text annotations
    5. Saves the resulting DXF file
    
    Args:
        pdf_path (str): Path to input PDF file
        output_path (str): Path for output DXF file
    
    Returns:
        dict: Conversion results containing:
              - 'success': bool indicating success/failure
              - 'output_file': path to saved DXF file
              - 'total_entities': total number of entities created
              - 'pages_processed': number of pages converted
    
    Coordinate System Notes:
        PDF: Origin bottom-left, Y increases upward but values decrease in interpretation
        DXF: Origin bottom-left, Y increases upward with increasing values
        Conversion: Y_dxf = page_height - Y_pdf
    
    Example:
        >>> result = convert_pdf_to_dxf("floorplan.pdf", "output.dxf")
        >>> print(f"Created {result['total_entities']} entities")
    """
    try:
        # Open PDF document
        doc = fitz.open(pdf_path)
        print(f"📄 Opened PDF: {pdf_path}")
        print(f"   Pages: {len(doc)}")
        
        # Create DXF document with layers
        dxf_doc, msp = create_dxf_document_with_layers()
        
        pages_processed = 0
        
        # Process each page
        for page in doc:
            print(f"\n🔄 Processing Page {page.number}...")
            page_height = page.rect.height
            
            # Extract drawing elements
            drawings = page.get_drawings()
            print(f"   Found {len(drawings)} drawing elements")
            
            # Analyze element types
            type_counter = analyze_drawing_elements(drawings)
            print("   🔎 Drawing elements by type:")
            for shape_type, count in type_counter.items():
                print(f"      - '{shape_type}': {count} element(s)")
            
            # Convert geometry elements
            geometry_stats = convert_geometry_elements(drawings, page_height, msp)
            print(f"   ✓ Converted geometry: {sum(geometry_stats.values())} elements")
            
            # Extract and convert text
            text_count = extract_and_convert_text(page, page_height, msp)
            print(f"   ✓ Extracted text: {text_count} text entities")
            
            pages_processed += 1
        
        # Print statistics
        print_dxf_statistics(dxf_doc, msp)
        
        # Save DXF file
        dxf_doc.saveas(output_path)
        print(f"\n🎉 DXF saved as: {output_path}")
        
        return {
            'success': True,
            'output_file': output_path,
            'total_entities': len(msp),
            'pages_processed': pages_processed
        }
    
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# Configuration: proximity threshold for determining if line endpoints are connected
# This value depends on your PDF scale and DXF units
# Smaller values = stricter connection requirements (lines must be very close)
# Larger values = more lenient (lines further apart will be considered connected)
PROXIMITY_THRESHOLD = 1.0  # units depend on your PDF scale


def is_close(p1, p2, tol=1.0):
    """
    Check if two points are within a specified tolerance distance.
    
    Used to determine if line endpoints are close enough to be considered
    connected, accounting for small gaps or slight misalignments in PDF geometry.
    
    Args:
        p1 (tuple or Vec2): First point (x, y)
        p2 (tuple or Vec2): Second point (x, y)
        tol (float): Maximum distance for points to be considered "close" (default: 1.0)
    
    Returns:
        bool: True if Euclidean distance between points <= tolerance, False otherwise
    
    Example:
        >>> is_close((0, 0), (0.5, 0.5), tol=1.0)
        True  # Distance is ~0.71, which is < 1.0
        >>> is_close((0, 0), (5, 5), tol=1.0)
        False  # Distance is ~7.07, which is > 1.0
    
    Note:
        Uses ezdxf Vec2 for vector arithmetic and magnitude calculation.
    """
    # Convert points to Vec2 objects and calculate Euclidean distance
    # magnitude = sqrt((x2-x1)² + (y2-y1)²)
    return (Vec2(p1) - Vec2(p2)).magnitude <= tol


def build_line_graph(entities, tol=1.0):
    """
    Build a connectivity graph from DXF line entities based on endpoint proximity.
    
    Creates a graph structure where line endpoints are nodes and edges exist
    when endpoints are within tolerance distance. This allows grouping of
    disconnected line segments that should form continuous walls or boundaries.
    
    Args:
        entities (list): List of DXF entities from modelspace
        tol (float): Proximity tolerance for connecting endpoints (default: 1.0)
    
    Returns:
        tuple: (lines, connections)
            - lines (list of tuple): [(start_point, end_point), ...] for each line
            - connections (defaultdict): {point: [connected_points]} adjacency list
    
    Graph structure:
        connections = {
            (x1, y1): [(x2, y2), (x3, y3)],  # Point (x1,y1) connects to two other points
            (x2, y2): [(x1, y1), (x4, y4)],  # Point (x2,y2) connects to two other points
            ...
        }
    
    Example:
        >>> lines, graph = build_line_graph(msp, tol=1.0)
        >>> # graph[(10, 20)] returns all points connected to (10, 20)
    
    Use case:
        After PDF-to-DXF conversion, individual wall segments may be separated
        by small gaps. This function identifies which line endpoints are close
        enough to be considered connected, enabling wall boundary reconstruction.
    
    Note:
        - Only processes LINE entities (ignores circles, arcs, text, etc.)
        - Each line creates two entries in connections (one for each endpoint)
        - Uses tuple(Vec2) for hashable dictionary keys
    """
    # Initialize adjacency list for graph structure
    connections = defaultdict(list)
    
    # Store all line segment data
    lines = []
    
    # Process each entity in the DXF document
    for e in entities:
        # Filter: only process LINE entities
        if e.dxftype() == 'LINE':
            # Extract start and end points as Vec2 objects
            start = Vec2(e.dxf.start)
            end = Vec2(e.dxf.end)
            
            # Store line segment
            lines.append((start, end))
            
            # Add bidirectional connections to graph
            # Connection from start -> end
            connections[tuple(start)].append(tuple(end))
            
            # Connection from end -> start (graph is undirected)
            connections[tuple(end)].append(tuple(start))
    
    return lines, connections

if __name__ == '__main__':
    # Configuration
    pdf_path = "examples/FloorplansAndSectionViews/Simple Floorplan/01_Simple.pdf"
    # pdf_path = "examples/FloorplansAndSectionViews/BasicTestPlan.pdf"
    
    output_path = "converted_output_with_text_and_curves.dxf"
    
    # Run conversion
    result = convert_pdf_to_dxf(pdf_path, output_path)
    
    if result['success']:
        print(f"\n✅ Conversion completed successfully!")
        print(f"   Output: {result['output_file']}")
        print(f"   Total entities: {result['total_entities']}")
        print(f"   Pages processed: {result['pages_processed']}")
    else:
        print(f"\n❌ Conversion failed: {result.get('error', 'Unknown error')}")

    