import os
from typing import Tuple, List
import pymupdf  
def convert_pdf2img(input_file: str, pages: Tuple = None):
    """Converts pdf to image and generates a file by page"""
    # Open the document
    pdfIn = pymupdf.open(input_file)
    # Iterate throughout the pages
    for pg in range(pdfIn.page_count):
        if str(pages) != str(None):
            if str(pg) not in str(pages):
                continue
        # Select a page
        page = pdfIn[pg]
        rotate = int(0)
        # PDF Page is converted into a whole picture 1056*816 and then for each picture a screenshot is taken.
        # zoom = 1.33333333 -----> Image size = 1056*816
        # zoom = 2 ---> 2 * Default Resolution (text is clear, image text is hard to read)    = filesize small / Image size = 1584*1224
        # zoom = 4 ---> 4 * Default Resolution (text is clear, image text is barely readable) = filesize large
        # zoom = 8 ---> 8 * Default Resolution (text is clear, image text is readable) = filesize large
        zoom_x = 2
        zoom_y = 2
        # The zoom factor is equal to 2 in order to make text clear
        # Pre-rotate is to rotate if needed.
        mat = pymupdf.Matrix(zoom_x, zoom_y).prerotate(rotate)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        output_file = f"{os.path.splitext(os.path.basename(input_file))[0]}_page{pg+1}.png"
        pix.save(output_file)
    pdfIn.close()
    summary = {
        "File": input_file, "Pages": str(pages), "Output File(s)": str(output_file)
    }
    # Printing Summary
    print("## Summary ########################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
    print("###################################################################")
    return output_file


######## Chunking ############

def pdf_to_split_images(path, page_number):
    from PIL import Image
    import io
    """
    Convert a pymupdf page to high-res image and split into 4 pieces.
    Args:
        path: path to PDF file
        page_number: page number
    Returns:
        List of 4 file paths to saved PNG images
    """
    doc = pymupdf.open(path)
    page = doc[page_number]
    
    # Render page to pixmap (image)
    pix = page.get_pixmap(dpi=300)
    
    # Convert to PIL Image
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    
    # Get dimensions
    width, height = img.size
    quarter_of_height = (1/4)*height
    sec_quarter_of_height = (1/2)*height
    third_quarter_of_height = (3/4)*height
    overlap = int(0.1 * height)
    # Split into 3 pieces
    chunks = [
        img.crop((0, 0, width, quarter_of_height+overlap)),          #upper third
        img.crop((0, quarter_of_height-overlap, width, sec_quarter_of_height+overlap)),       # middle third
        img.crop((0, sec_quarter_of_height-overlap, width, third_quarter_of_height+overlap)),
        img.crop((0, third_quarter_of_height-overlap, width, height))  # bottom third
    ]
   
    
    # Save chunks to temporary files
    output_files = []
    base_name = os.path.splitext(os.path.basename(path))[0]
    
    for idx, chunk in enumerate(chunks):
        # Create temp file or save to specific directory
        output_file = f"{base_name}_page{page_number + 1}_chunk{idx + 1}.png"
        chunk.save(output_file)
        output_files.append(output_file)
    
    doc.close()
    return output_files


