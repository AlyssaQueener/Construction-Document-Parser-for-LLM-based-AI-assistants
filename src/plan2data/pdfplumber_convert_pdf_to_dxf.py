import pdfplumber
import ezdxf
from PIL import Image
if __name__=='__main__':
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    doc.layers.new('PDFLines') # add specific layers 
    doc.layers.new('PDFRects')
    doc.layers.new('PDF Splines')
    doc.layers.new('PDFCurves')
    doc.layers.new('PDFText')
 


    pdf_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        lines = page.lines
        rects = page.rects
        curves = page.curves
        images = page.images
        chars = page.chars
        print(f"Lines detected: {len(lines)}")
        print(f"Rectangles detected: {len(rects)}")
        print(f"Curves detected: {len(curves)}")
        print(f"Images detected: {len(images)}")
        print(f"Characters detected: {len(chars)}")
    # for i, img_obj in enumerate(page.images):
    #     print(f"\nImage {i+1}:")
    #     print(img_obj)  # prints metadata like x0, y0, x1, y1, width, height

    #     # Render the full page to an image
    #     pil_image = page.to_image(resolution=150).original

    #     # Crop to the image area
    #     left = img_obj['x0']
    #     top = page.height - img_obj['y1']
    #     right = img_obj['x1']
    #     bottom = page.height - img_obj['y0']

    #     cropped_image = pil_image.crop((left, top, right, bottom))
    #     cropped_image.show(title=f"Image {i+1}")

    #to flip y achsis 
    page_height = page.height 
    
    for line in lines:
        x0, y0 = line['x0'], page_height - line['y0']
        x1, y1 = line['x1'], page_height - line['y1']
        msp.add_line((x0, y0), (x1, y1),dxfattribs={"layer": "PDFLines"})

    # Add rectangles (as LWPolylines)
    for rect in rects:
        x0, y0 = rect['x0'], page_height - rect['y0']
        x1, y1 = rect['x1'], page_height - rect['y1']
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],dxfattribs={"layer": "PDFRects"}, close=True)
    for curve in page.curves:
            print(curve['pts'])
            if 'pts' in curve:
                points = [
                    (pt[0], page.height - pt[0]) for pt in curve['pts']
                ]
                msp.add_lwpolyline(points, dxfattribs={"layer": "PDFCurves"})
            else:
            # Fallback: Just use start and end points
                points = [
                    (curve['x0'], page.height - curve['y0']),
                    (curve['x1'], page.height - curve['y1']),
                ]
                msp.add_lwpolyline(points, dxfattribs={"layer": "PDFCurves"})
    for char in page.chars:
        x = char['x0']
        y = page.height - char['top']  # Flip Y
        text = char['text']
        msp.add_text(text, dxfattribs={'height': char['size'], 'insert':(x, y),"layer": "PFDText"})
    # Save DXF
    doc.saveas("output.dxf")