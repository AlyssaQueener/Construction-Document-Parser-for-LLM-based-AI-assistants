import pymupdf
import fitz  # PyMuPDF
from PIL import Image
import os
import pytesseract
import google.generativeai as genai 





def extract_title_block(pdf_path, bbox_region="bottom_right"):
    doc = fitz.open(pdf_path)
    first_page = doc[0]  # assuming title block is on the first page

    # Get page size to define region
    width, height = first_page.rect.width, first_page.rect.height
    
    # Define Plankopf region (e.g., bottom right corner, last 5 cm)
    margin = 50  # adjust based on units (points: 72pt = 1 inch)
    if bbox_region == "bottom_right":
        region = fitz.Rect(width - margin*4, height - margin, width, height)
    else:
        raise NotImplementedError("Only bottom_right supported for now")

    # Extract text in region
    text_blocks = first_page.get_text("blocks")
    title_block_text = [b for b in text_blocks if fitz.Rect(b[:4]).intersects(region)]
    
    return title_block_text

if __name__ == "__main__":
    
# create object page from directry########################
    pdf_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf.pdf"
    output_folder = "examples/FloorplansAndSectionViews/output/cropped_boxes"
    os.makedirs(output_folder, exist_ok=True)

    doc = pymupdf.open(pdf_path)  # or pymupdf.Document(filename)
    page = doc.load_page(0)  # loads page number 'pno' of the document (0-based)
    # Extract text ##########################
    blocks = page.get_text("blocks")
    #print(blocks)
    
    # Assume plan is landscape — plankopf often on the far right 
    page_width, page_height = page.rect.width, page.rect.height
    candidate_blocks = [
        b for b in blocks if b[0] > page_width * 0.7 
    ]
    # Merge into one bounding box covering all text
    if candidate_blocks:  
        dense_area = fitz.Rect(candidate_blocks[0][:4]) # b[:4] = Take the first 4 elements from list or tuple b-> retuns bounding box coordinates 
        #(x0, y0, x1, y1, "text", block_id, line_id) becomes (x0, y0, x1, y1) rect creates and rectangle out of the coordinates 
        for b in candidate_blocks[1:]: #This takes all blocks except the first one, because the first one was already used to initialize dense_area.
            dense_area |= fitz.Rect(b[:4]) #|= is shorthand for union It expands dense_area to include the new rectangle
    # Expand margins
    dense_area.x0 -= 10
    dense_area.y0 -= 20
    dense_area.x1 += 10
    dense_area.y1 += 20

    # render cropped area to an image 
    zoom = 2  # resolution scaling
    mat = fitz.Matrix(zoom, zoom)
    clip = dense_area  # the bounding box
    pix = page.get_pixmap(matrix=mat, clip=clip)
    pix.save("examples/FloorplansAndSectionViews/output/cropped_boxes/dense_text_region.png")
   
    #save remaining plan in a seperate image ##################################################
    # Create complementary bounding box — left side of the page (excluding dense text area)
    remaining_area = fitz.Rect(
        0,                      # x0: start of page
        0,                      # y0: start of page
        dense_area.x0,          # x1: left edge of the dense text region
        page_height             # y1: full page height
    )  

    # Optional: add some small margin, if needed
    remaining_area.x1 -= 10

    # Render remaining plan area to image
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    clip_remaining = remaining_area

    pix_remaining = page.get_pixmap(matrix=mat, clip=clip_remaining)
    pix_remaining.save("examples/FloorplansAndSectionViews/output/cropped_boxes/remaining_plan_area.png")
#########################################################################################################
     # extract text from image ################
    img = Image.open("examples/FloorplansAndSectionViews/output/cropped_boxes/dense_text_region.png")  # your cropped image
    text = pytesseract.image_to_string(img, lang="deu")#,config="--psm 11")  # use 'eng' or 'deu' depending on content
    print(text)

    
#  ###########################################################################################
#  # Look for a keyword 
#     areas = page.search_for("Plan")
#     #print(areas)
# # highlight areas ####################################################################
#     # for rect in areas:
#     #     highlight = page.add_highlight_annot(rect)
#     #     highlight.update()  # finalize the annotation

#     # # Save the result to a new PDF
#     # output_path = "examples/FloorplansAndSectionViews/output/highlighted_plan.pdf"
#     # doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
#     # print(f"Highlights saved to: {output_path}")

# # print text boxes ######################################################
#     for i, rect in enumerate(areas):
#         text = page.get_textbox(rect)
#         print(f"Box {i+1} at {rect}:\n{text}\n{'-'*40}")
# # cropp and create image 
# # Render the page to an image
#     # zoom = 2  # for higher resolution
#     # mat = fitz.Matrix(zoom, zoom)
#     # pix = page.get_pixmap(matrix=mat)

#     # # Convert full page to PIL image
#     # img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

#     # Convert PDF coords to image coords and crop
#     # for i, rect in enumerate(areas):
#     #     # Scale the rect to match zoom level
#     #     scaled = fitz.Rect(rect.x0 * zoom, rect.y0 * zoom, rect.x1 * zoom, rect.y1 * zoom)

#     #     # Crop region from full image
#     #     cropped = img.crop((scaled.x0, scaled.y0, scaled.x1, scaled.y1))

#     #     # Save cropped image
#     #     cropped_path = os.path.join(output_folder, f"box_{i+1}.png")
#     #     cropped.save(cropped_path)
#     #     print(f"Saved: {cropped_path}")





    # crop all pictures 
    # for i, block in enumerate(blocks):
    #     rect = fitz.Rect(block[0], block[1], block[2], block[3])  # (x0, y0, x1, y1)
    #     pix = page.get_pixmap(clip=rect, dpi=300)

    #     cropped_path = os.path.join(output_folder, f"box_{i+1}.png")
    #     pix.save(cropped_path)
    #     print(f"Saved: {cropped_path}")
# exctract images ######################
    # drawing = page.get_drawings()
    # #print(drawing)
    # for item in drawing:
    #     if item['type'] == 's':
    #         print(item['rect'])
