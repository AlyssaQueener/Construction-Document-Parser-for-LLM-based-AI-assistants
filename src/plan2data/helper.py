import os
import io
from typing import Tuple
import pymupdf  
import json
from PIL import Image
import src.plan2data.mistralConnection as mistral


def extract_images_from_pdf(path_pdf, output_format, output_dir):
    # Minimum width and height for extracted images
    min_width = 10
    min_height = 10
    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    pdf_file = pymupdf.open(path_pdf)
    # Iterate over PDF pages
    for page_index in range(len(pdf_file)):
        # Get the page itself
        page = pdf_file[page_index]
        # Get image list
        image_list = page.get_images(full=True)
        # Print the number of images found on this page
        if image_list:
            print(f"[+] Found a total of {len(image_list)} images in page {page_index}")
        else:
            print(f"[!] No images found on page {page_index}")
        # Iterate over the images on the page
        for image_index, img in enumerate(image_list, start=1):
            # Get the XREF of the image
            xref = img[0]
            # Extract the image bytes
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]
            # Get the image extension
            image_ext = base_image["ext"]
            # Load it to PIL
            image = Image.open(io.BytesIO(image_bytes))
            # Check if the image meets the minimum dimensions and save it
            if image.width >= min_width and image.height >= min_height:
                image.save(
                    open(os.path.join(output_dir, f"image{page_index + 1}_{image_index}.{output_format}"), "wb"),
                    format=output_format.upper())
            else:
                print(f"[-] Skipping image {image_index} on page {page_index} due to its small size.")

def convert_pdf2img(input_file: str, pages: Tuple = None):
    """Converts pdf to image and generates a file by page"""
    # Open the document
    pdfIn = pymupdf.open(input_file)
    output_files = []
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
        pix = page.get_pixmap(dpi=300)
        output_file = f"{os.path.splitext(os.path.basename(input_file))[0]}_page{pg+1}.png"
        pix.save(output_file)
        output_files.append(output_file)
    pdfIn.close()
    summary = {
        "File": input_file, "Pages": str(pages), "Output File(s)": str(output_files)
    }
    # Printing Summary
    print("## Summary ########################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
    print("###################################################################")
    return output_files

############# room extraction voronoi #################
def pdf_to_split_images(path, page_number):
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
    mid_w = width // 2
    mid_h = height // 2
    
    # Split into 4 pieces
    chunks = [
        img.crop((0, 0, mid_w, mid_h)),           # top_left
        img.crop((mid_w, 0, width, mid_h)),       # top_right
        img.crop((0, mid_h, mid_w, height)),      # bottom_left
        img.crop((mid_w, mid_h, width, height))   # bottom_right
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

def page_to_split_images(page):
    """
    Convert a pymupdf page to high-res image and split into 4 pieces.
    Args:
        path: path to PDF file
        page_number: page number
    Returns:
        List of 4 file paths to saved PNG images
    """
    # Render page to pixmap (image)
    pix = page.get_pixmap(dpi=300)
    
    # Convert to PIL Image
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    
    # Get dimensions
    width, height = img.size
    mid_w = width // 2
    mid_h = height // 2
    
    # Split into 4 pieces
    chunks = [
        img.crop((0, 0, mid_w, mid_h)),           # top_left
        img.crop((mid_w, 0, width, mid_h)),       # top_right
        img.crop((0, mid_h, mid_w, height)),      # bottom_left
        img.crop((mid_w, mid_h, width, height))   # bottom_right
    ]
    
    # Save chunks to temporary files
    output_files = []
    base_name = os.path.splitext(os.path.basename(path))[0]
    
    for idx, chunk in enumerate(chunks):
        # Create temp file or save to specific directory
        output_file = f"{base_name}_page{page_number + 1}_chunk{idx + 1}.png"
        chunk.save(output_file)
        output_files.append(output_file)
    
    return output_files


def extract_room_names_from_chunks(chunked_plan):
    """
    Extract room names from image chunks and clean up files afterward.
    Args:
        chunked_plan: List of file paths to image chunks
    Returns:
        List of room names extracted from each chunk
    """
    all_room_names = []
    
    try:
        for image_path in chunked_plan:
            rooms_json = mistral.call_mistral_for_room_extraction_voronoi(image_path)
            try:
                rooms_list = json.loads(rooms_json)
                all_room_names.extend(rooms_list)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse JSON from {image_path}: {e}")
                print(f"Raw response: {rooms_json}")
                continue
    finally:
        # Clean up: delete all temporary image files
        for image_path in chunked_plan:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"Deleted: {image_path}")
            except Exception as e:
                print(f"Warning: Could not delete {image_path}: {e}")
    
    return all_room_names

###########################################################################
def check_for_further_ai_usage(ai_response):
    ai_response_as_dict = json.loads(ai_response)
    if ai_response_as_dict["Completness"] == "yes":
        return True
    else:
        return False


## Determines based on ai response in which quadrant of the image the titleblock is located by returning the horizontal and vertical boundry
## and wether the location of the titleblock is below/above the vertical and right/left of horizontal boundry 
def prepare_for_titleblock_extraction(ai_response):
    ai_response_as_dict = json.loads(ai_response)
    
    vertical_from = float(ai_response_as_dict["Vertical location"]["From"])
    vertical_to = float(ai_response_as_dict["Vertical location"]["To"])
    horizontal_from = float(ai_response_as_dict["Horizontal location"]["From"])
    horizontal_to = float(ai_response_as_dict["Horizontal location"]["To"])
    
    vertical_center = (vertical_from + vertical_to) / 2
    horizontal_center = (horizontal_from + horizontal_to) / 2
    
    greater_then_vertical = vertical_center >= 0.5
    greater_then_horizontal = horizontal_center >= 0.5
    
    if greater_then_vertical:
        vertical_boundary_percentage = vertical_from  
    else:
        vertical_boundary_percentage = vertical_to    
        
    if greater_then_horizontal:
        horizontal_boundary_percentage = horizontal_from  
    else:
        horizontal_boundary_percentage = horizontal_to   

    ## in the case that the title block located over full image height/ width
    ## greater_then_vertical/ the_horizontal is true but the vertical/horizontal_from value is 0
    ## this is problematic in the title_block_region function because the boundry value is set to zero
    ## therefore text block regions are not recognized
    ## workaround: set boundry percentage values to 1 instead of 0

    if horizontal_boundary_percentage == 0.0 and greater_then_horizontal == True:
        horizontal_boundary_percentage = 1
        greater_then_horizontal = False
    if vertical_boundary_percentage == 0.0 and greater_then_vertical == True:
        greater_then_vertical = False
        vertical_boundary_percentage = 1
    

    return horizontal_boundary_percentage, vertical_boundary_percentage, greater_then_horizontal, greater_then_vertical


