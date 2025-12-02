import os
from typing import Tuple
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
    # Split into 4 pieces
    chunks = [
        img.crop((0, 0, width, quarter_of_height+overlap)),          
        img.crop((0, quarter_of_height-overlap, width, sec_quarter_of_height+overlap)),       
        img.crop((0, sec_quarter_of_height-overlap, width, third_quarter_of_height+overlap)),
        img.crop((0, third_quarter_of_height-overlap, width, height)) 
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

def pdf_to_split_images_with_timeline(path, page_number, timeline_height_ratio=0.15):
    from PIL import Image
    import io
    """
    Convert a pymupdf page to high-res image and split into chunks,
    including the timeline header in each chunk.
    
    Args:
        path: path to PDF file
        page_number: page number
        timeline_height_ratio: proportion of page height that contains the timeline (default 0.15 = 15%)
    
    Returns:
        List of file paths to saved PNG images with timeline included
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
    
    # Extract timeline (top portion of the chart)
    timeline_height = int(timeline_height_ratio * height)
    timeline = img.crop((0, 0, width, timeline_height))
    
    # Calculate remaining content area
    content_start = timeline_height
    content_height = height - timeline_height
    
    # Define overlap for smooth transitions
    overlap = int(0.1 * content_height)
    
    # Split content into chunks
    quarter = content_height / 4
    
    chunk_boundaries = [
        (content_start, content_start + quarter),
        (content_start + quarter, content_start + 2 * quarter),
        (content_start + 2 * quarter, content_start + 3 * quarter),
        (content_start + 3 * quarter, height)
    ]
    
    chunks = []
    for i, (start, end) in enumerate(chunk_boundaries):
        # Adjust for overlap (except first and last)
        chunk_start = max(content_start, start - overlap)
        chunk_end = min(height, end + overlap)
        
        # Extract content chunk
        content_chunk = img.crop((0, chunk_start, width, chunk_end))
        
        # Create new image with timeline on top
        combined_height = timeline_height + content_chunk.height
        combined = Image.new('RGB', (width, combined_height), 'white')
        
        # Paste timeline at top
        combined.paste(timeline, (0, 0))
        
        # Paste content below timeline
        combined.paste(content_chunk, (0, timeline_height))
        
        chunks.append(combined)
    
    # Save chunks to files
    output_files = []
    base_name = os.path.splitext(os.path.basename(path))[0]
    
    for idx, chunk in enumerate(chunks):
        output_file = f"{base_name}_page{page_number + 1}_chunk{idx + 1}.png"
        chunk.save(output_file)
        output_files.append(output_file)
    
    doc.close()
    return output_files