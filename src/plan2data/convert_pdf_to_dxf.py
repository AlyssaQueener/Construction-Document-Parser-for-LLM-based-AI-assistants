import ezdxf.math
import fitz  # PyMuPDF
import ezdxf #https://ezdxf.readthedocs.io/en/stable/concepts/coordinates.html#wcs
from collections import defaultdict
from collections import Counter



# add layer explicitly like 
#dxf_doc.layers.new('PDFLines')
#dxf_doc.layers.new('TextLayer')
if __name__=='__main__':
    pdf_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf.pdf"
    #pdf_path= "examples/FloorplansAndSectionViews/BasicTestPlan.pdf"
    doc = fitz.open(pdf_path)
    # difference between dxf and pdf coordinates 
    #pdf Ursprung unten links, y läuft nach oben aber nimmt nach oben ab in der interpretation??? https://www.datalogics.com/pdf-rendering-coordinate-systems?
    #dxf Ursprung unten links, y läuft nach oben aber nimmt nach oben zu

# create dxf doc and create layers 
    dxf_doc = ezdxf.new() # create a new dxf document 
    dxf_doc.layers.new('PDFLines') # add specific layers 
    dxf_doc.layers.new('PDFRects')
    dxf_doc.layers.new('PDFSplines')
    dxf_doc.layers.new('PDFCurves')
    dxf_doc.layers.new('PDFText')
    dxf_doc.layers.new('PDFFilledshapes')
    dxf_doc.layers.new('PDFQuads')
    msp = dxf_doc.modelspace() # getting the modelspüace of an dxf document 
    #psp = dxf_doc.paperspace("layout 1")

# export geometry primitives from pymupdf 
    for page in doc:
        page_height = page.rect.height
        line_segments = []
        drawings = page.get_drawings()
        print(f"Page {page.number}: Found {len(drawings)} drawing elements.")
        
        # identify number of items of each type 
        type_counter = Counter()
        
        for item in drawings:
            #print(item)
            # pdf_layer = item.get("layer")
            # if pdf_layer:
            #     print(f"PDF Layer found: {pdf_layer}")
            # else:
            #     print("No PDF layer (probably default or flattened).")
            for element in item["items"]:
            #     if element[0] == 's':
            #         print(element) 
            #         print("the length of the elemnt is")
            #         print(len(element))
                if isinstance(element, (list, tuple)) and len(element) > 0:
                    shape_type = element[0]
                    type_counter[shape_type] += 1

        print("🔎 Drawing elements by type:")
        for shape_type, count in type_counter.items():
            print(f"  - '{shape_type}': {count} element(s)")


# convert items to dxf items and add them to modelspace 
        for item in drawings:
        #     print(f"Type: {item.get('type')}, Items count: {len(item['items'])}")
            for element in item["items"]:
                if not isinstance(element, (list, tuple)):
                    continue
                
                if element[0] == "l" and len(element) == 3:
                        _, p1, p2 = element
                        pt1 = (round(p1.x, 2), round(page_height - p1.y, 2))
                        pt2 = (round(p2.x, 2), round(page_height - p2.y, 2))
                        line_segments.append((pt1, pt2))
                        msp.add_line((pt1),(pt2),dxfattribs={"layer": "PDFLines"},)
                    
                elif element[0] == "re" and len(element) == 3:
                    _, rect,fill = element
                    x0, y0 = rect.x0, rect.y0
                    x1, y1 = rect.x1, rect.y1
                    
                    # Transform Y coordinates
                    y0_dxf = page_height - y0
                    y1_dxf = page_height - y1
                    
                    x_min, x_max = min(x0, x1), max(x0, x1)
                    y_min, y_max = min(y0_dxf, y1_dxf), max(y0_dxf, y1_dxf)
                        
                    msp.add_solid(
                        [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)],
                            dxfattribs={"layer": "PDFRects"}
                        )
                    
                # # elif element[0] == "c" and len(element) == 5:
                # #     _, p0,p1,p2,p3 = element
                # #     # Try to approximate as arc if possible
                # #     try:
                # #         arc = ezdxf.math.ConstructionArc([p1, p2, p3])
                # #         msp.add_arc(
                # #             center=(arc.center.x, page_height - arc.center.y),
                # #             radius=arc.radius,
                # #             start_angle=arc.start_angle,
                # #             end_angle=arc.end_angle,
                # #             dxfattribs={"layer": "PDFCurves"}
                # #         )
                #     except ValueError:
                #         # fallback: treat as spline if not arc
                #         points = [(p1.x, page_height - p1.y), (p2.x, page_height - p2.y), (p3.x, page_height - p3.y)]
                #         msp.add_spline(points, dxfattribs={"layer": "PDFSplines"})
                #         print("⚠️ Could not construct arc; falling back to spline.")
                elif element[0] == "el" and len(element) == 2:
                    _, ellipse = element
                    cx, cy = ellipse.center
                    rx, ry = ellipse.rx, ellipse.ry  # radii
                    rotation = ellipse.rotation
                    if abs(rx - ry) < 1e-3:  # approximate as circle
                            msp.add_circle(center=(cx, page_height - cy), radius=rx, dxfattribs={"layer": "PDFCurves"})
                    else:
                            msp.add_ellipse(
                                center=(cx, page_height - cy),
                                major_axis=(rx, 0),
                                ratio=ry / rx,
                                dxfattribs={"layer": "PDFCurves"}
                            )
                elif element[0] == 'f' and isinstance(element[1], list):
                    filled_path = element[1]
                    if len(filled_path) >= 3:
                            points = [(pt.x, page_height - pt.y) for pt in filled_path]
                            # Option 1: As closed polyline
                            msp.add_lwpolyline(points, dxfattribs={"layer": "PDFFilledshapes"}, close=True)
                            # Option 2 (alternative): as SPLINE (useful for smooth shapes)
                            # msp.add_spline(points, dxfattribs={"layer": "PDFCurves"})
                elif element[0] == 'qu' and len(element) == 2:
                    _, quad = element 
                    p0,p1,p2,p3 = quad
                    points = [  (p0.x, page_height - p0.y),
                                (p1.x, page_height - p1.y),
                                (p3.x, page_height - p3.y),
                                (p2.x, page_height - p2.y),
                                (p0.x, page_height - p0.y),]  # quad strucutre TopLeft, BottomLeft, TopRight, BottomRight

    
                    msp.add_lwpolyline(points, dxfattribs={"layer": "PDFQuads"})
    # === Text Extraction ===
    textpage = page.get_textpage()
    text_dict = textpage.extractDICT()
    page_height = page.rect.height

    for block in text_dict["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    x, y = span["origin"]
                    text = span["text"]
                    font_height = span["size"]
                    
                    # Convert Y to DXF coordinates
                    dxf_y = page_height - y

                    text_entity = msp.add_text(text, dxfattribs={
                        "height": font_height,
                        "layer": "PDFText"
                    })
                    text_entity.dxf.insert = (x, dxf_y)
    

  

    # === Save and Report ===
    # print(f"✅ Total entities in modelspace: {len(msp)}")
    # for entity in msp:
    #     print(f"{entity.dxftype()} on layer {entity.dxf.layer}")

    for layer in dxf_doc.layers:
        print(f"Layer: {layer.dxf.name}")

    # Count how many entities are on each layer
    layer_counts = Counter()
    for entity in msp:
        layer_counts[entity.dxf.layer] += 1

    # Print the count per layer
    # print("\n📊 Entity count per layer:")
    for layer, count in layer_counts.items():
        print(f"  - {layer}: {count} entities")
    dxf_doc.saveas("converted_output_with_text_and_curves.dxf")
    print("🎉 DXF with curves and text saved as converted_output_with_text_and_curves.dxf")        
    print(f"✅ Total entities in modelspace: {len(msp)}")
    #print(f"Grouped into {len(polylines)} polylines from {len(line_segments)} lines.")

