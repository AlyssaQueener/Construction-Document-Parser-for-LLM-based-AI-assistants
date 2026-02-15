import os
import io
from typing import Tuple
import pymupdf
import json
from PIL import Image

import src.plan2data.mistralConnection as mistral


###############################################################################
# PDF Image & Page Utilities
#
# Functions for extracting embedded images from PDFs, converting PDF pages
# to high-resolution raster images, and splitting pages into chunks for
# downstream AI processing (e.g. room name extraction).
###############################################################################


def extract_images_from_pdf(path_pdf, output_dir, output_format="png"):
    """
    Extract all embedded raster images from a PDF and save them to disk.

    Iterates through every page, pulls out each embedded image via its XREF
    (cross-reference ID in the PDF object table), and writes it to
    `output_dir` if it meets a minimum size threshold.

    Args:
        path_pdf:       Path to the source PDF file.
        output_format:  Target image format for saved files (e.g. "png", "jpeg").
        output_dir:     Directory where extracted images will be written.
    """
    min_width = 10
    min_height = 10

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_file = pymupdf.open(path_pdf)

    for page_index in range(len(pdf_file)):
        page = pdf_file[page_index]
        image_list = page.get_images(full=True)

        if image_list:
            print(f"[+] Found a total of {len(image_list)} images in page {page_index}")
        else:
            print(f"[!] No images found on page {page_index}")

        for image_index, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]

            image = Image.open(io.BytesIO(image_bytes))

            if image.width >= min_width and image.height >= min_height:
                image.save(
                    open(
                        os.path.join(output_dir, f"image{page_index + 1}_{image_index}.{output_format}"),
                        "wb",
                    ),
                    format=output_format.upper(),
                )
            else:
                print(f"[-] Skipping image {image_index} on page {page_index} due to its small size.")


def convert_pdf2img(input_file: str, pages: Tuple = None):
    """
    Render selected (or all) PDF pages as high-resolution PNG images.

    Each page is rasterized at 300 DPI and saved as a separate file in the
    current working directory. Useful for feeding full-page images into
    OCR or vision-based AI pipelines.

    Args:
        input_file: Path to the source PDF.
        pages:      Optional tuple of page numbers to convert. If None,
                    all pages are converted.

    Returns:
        A list of output file paths for the generated PNGs.
    """
    pdfIn = pymupdf.open(input_file)
    output_files = []

    for pg in range(pdfIn.page_count):
        if str(pages) != str(None):
            if str(pg) not in str(pages):
                continue

        page = pdfIn[pg]
        # Render at 300 DPI for high-quality output suitable for OCR
        pix = page.get_pixmap(dpi=300)

        output_file = f"{os.path.splitext(os.path.basename(input_file))[0]}_page{pg+1}.png"
        pix.save(output_file)
        output_files.append(output_file)

    pdfIn.close()

    summary = {
        "File": input_file,
        "Pages": str(pages),
        "Output File(s)": str(output_files),
    }
    return output_files


###############################################################################
# Room Extraction via Voronoi — Image Splitting Strategy - Future Work
#
# Large architectural drawings often exceed what a vision model can process
# in one pass. These functions split a page into 4 quadrant chunks so each
# piece can be sent to Mistral individually for room name detection.
###############################################################################


def pdf_to_split_images(path, page_number):
    """
    Render a single PDF page at 300 DPI and split it into 4 equal quadrants.

    The quadrants (top-left, top-right, bottom-left, bottom-right) are saved
    as individual PNG files for independent processing.

    Args:
        path:        Path to the PDF file.
        page_number: Zero-based page index to render and split.

    Returns:
        List of 4 file paths to the saved quadrant PNGs.
    """
    doc = pymupdf.open(path)
    page = doc[page_number]

    # Render at 300 DPI for sufficient detail to read room labels
    pix = page.get_pixmap(dpi=300)

    # Convert PyMuPDF pixmap → PIL Image for easy cropping
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))

    # Calculate the midpoint for a 2×2 grid split
    width, height = img.size
    mid_w = width // 2
    mid_h = height // 2

    # Crop into 4 quadrants
    chunks = [
        img.crop((0, 0, mid_w, mid_h)),          # top-left
        img.crop((mid_w, 0, width, mid_h)),       # top-right
        img.crop((0, mid_h, mid_w, height)),      # bottom-left
        img.crop((mid_w, mid_h, width, height)),  # bottom-right
    ]

    # Save each quadrant as a temporary PNG
    output_files = []
    base_name = os.path.splitext(os.path.basename(path))[0]

    for idx, chunk in enumerate(chunks):
        output_file = f"{base_name}_page{page_number + 1}_chunk{idx + 1}.png"
        chunk.save(output_file)
        output_files.append(output_file)

    doc.close()
    return output_files


def page_to_split_images(page):
    """
    Same quadrant-splitting logic as `pdf_to_split_images`, but accepts a
    PyMuPDF page object directly instead of a file path + page number.

    NOTE: This function currently has a bug — it calls `os.path.basename(page)`
    and `page + 1`, treating `page` as a string/int rather than a PyMuPDF
    page object. The naming logic needs to be fixed or a page identifier
    should be passed separately.

    Args:
        page: A pymupdf.Page object.

    Returns:
        List of 4 file paths to the saved quadrant PNGs.
    """
    pix = page.get_pixmap(dpi=300)

    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))

    width, height = img.size
    mid_w = width // 2
    mid_h = height // 2

    chunks = [
        img.crop((0, 0, mid_w, mid_h)),
        img.crop((mid_w, 0, width, mid_h)),
        img.crop((0, mid_h, mid_w, height)),
        img.crop((mid_w, mid_h, width, height)),
    ]

    output_files = []
    # BUG: `page` is a pymupdf.Page, not a file path — this will fail
    base_name = os.path.splitext(os.path.basename(page))[0]

    for idx, chunk in enumerate(chunks):
        output_file = f"{base_name}_page{page + 1}_chunk{idx + 1}.png"
        chunk.save(output_file)
        output_files.append(output_file)

    return output_files


def extract_room_names_from_chunks(chunked_plan):
    """
    Send each image chunk to Mistral for room name extraction, then
    clean up all temporary chunk files regardless of success or failure.

    Each chunk is processed independently and the results are merged into
    a single flat list. If Mistral returns invalid JSON for a chunk, that
    chunk is skipped with a warning rather than aborting the whole batch.

    Args:
        chunked_plan: List of file paths to quadrant image PNGs
                      (typically produced by `pdf_to_split_images`).

    Returns:
        A combined list of room name strings from all chunks.
    """
    all_room_names = []

    try:
        for image_path in chunked_plan:
            rooms_json = mistral.call_mistral_for_room_extraction_voronoi(image_path)

            try:
                rooms_list = json.loads(rooms_json)
                all_room_names.extend(rooms_list)
            except json.JSONDecodeError as e:
                # Non-fatal: log the error and continue with remaining chunks
                print(f"Warning: Could not parse JSON from {image_path}: {e}")
                print(f"Raw response: {rooms_json}")
                continue
    finally:
        # Always clean up temp files, even if an exception interrupted processing
        for image_path in chunked_plan:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"Deleted: {image_path}")
            except Exception as e:
                print(f"Warning: Could not delete {image_path}: {e}")

    return all_room_names





