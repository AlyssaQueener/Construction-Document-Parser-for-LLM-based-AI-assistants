import fitz  # PyMuPDF
import ezdxf

# add layer explicitly like 
#dxf_doc.layers.new('PDFLines')
#dxf_doc.layers.new('TextLayer')

pdf_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf.pdf"
doc = fitz.open(pdf_path)

dxf_doc = ezdxf.new()
msp = dxf_doc.modelspace()

for page in doc:
    drawings = page.get_drawings()
    print(f"Page {page.number}: Found {len(drawings)} drawing elements.")

    for item in drawings:
        print(f"Type: {item.get('type')}, Items count: {len(item['items'])}")
        
        for element in item["items"]:
            if not isinstance(element, (list, tuple)):
                continue
            if element[0] == "l" and len(element) == 3:
                _, p1, p2 = element
                msp.add_line((p1.x, p1.y), (p2.x, p2.y), dxfattribs={"layer": "PDFLines"})
            elif element[0] == "re" and len(element) == 2:
                _, rect = element
                x0, y0 = rect.x0, rect.y0
                x1, y1 = rect.x1, rect.y1
                msp.add_lwpolyline(
                    [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
                    dxfattribs={"layer": "PDFRects"},
                    close=True
                )
            elif element[0] == "c" and len(element) == 4:
                _, p1, p2, p3 = element
                points = [(p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y)]
                msp.add_spline(points, dxfattribs={"layer": "PDFCurves"})

    # === Text Extraction ===
    textpage = page.get_text("dict")
    for block in textpage["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    x, y = span["origin"]
                    text = span["text"]
                    font_height = span["size"]

                    text_entity=msp.add_text(text, dxfattribs={
                        "height": font_height,
                        "layer": "PDFText"
                    })
                    text_entity.dxf.insert = (x, y)
# === Save and Report ===
print(f"✅ Total entities in modelspace: {len(msp)}")
for entity in msp:
    print(f"{entity.dxftype()} on layer {entity.dxf.layer}")

for layer in dxf_doc.layers:
    print(f"Layer: {layer.dxf.name}")
dxf_doc.saveas("converted_output_with_text_and_curves.dxf")
print("🎉 DXF with curves and text saved as converted_output_with_text_and_curves.dxf")
        

print(f"✅ Total entities in modelspace: {len(msp)}")
dxf_doc.saveas("converted_output.dxf")
