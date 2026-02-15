import json
import src.plan2data.extractionLogictitleBlock as title_block_tesseract
import src.plan2data.mistralConnection as mistral
import src.plan2data.helper as helper


###############################################################################
# Title Block Extraction Workflow
#
# Extracts key metadata (e.g. project name, scale, date, architect) from the
# title block region of architectural floor plan images.
#
# Two strategies are used:
#   1. OCR-first (Tesseract): Locates the title block via rule-based logic,
#      extracts text with OCR, then sends it to Mistral for structuring.
#   2. AI-direct (Mistral vision): Sends the full image to Mistral, which
#      extracts content in one step.
#
# The primary entrypoint `get_title_block_info` tries the fast OCR path
# first and falls back to the AI path when confidence is too low.
###############################################################################


def get_title_block_info(path: str) -> dict | None:
    """
    Main entrypoint: extract title block metadata with automatic fallback.

    Attempts OCR-based extraction first. If the result is empty or the
    confidence score is below 0.6, falls back to full AI-based extraction.

    Args:
        path: File path to the floor plan image.

    Returns:
        A dict of extracted title block fields, or None if both methods fail.
    """
    output = json.loads(extract_title_block_info(path))

    # Fall back to AI if OCR returned nothing
    if not output:
        print("AI localization started")
        return json.loads(extract_title_block_info_with_ai(path))

    # Fall back to AI if OCR confidence is below the threshold
    if output["confidence"] < 0.6:
        print("AI localization started")
        return json.loads(extract_title_block_info_with_ai(path))

    return output


# ---------------------------------------------------------------------------
# Internal extraction functions
# ---------------------------------------------------------------------------


def extract_title_block_info(image_path):
    """
    OCR-based extraction pipeline.

    1. Uses Tesseract to locate and read text from the title block region.
    2. Sends the raw OCR text to Mistral to structure it into key-value pairs.

    Returns:
        JSON string of structured title block fields.
    """
    text_title_block = title_block_tesseract.extract_text_titleblock(image_path)
    mistral_response_content = mistral.call_mistral_for_content_extraction(text_title_block)
    return mistral_response_content


def extract_title_block_info_with_ai(image_path):
    """
    AI-based extraction pipeline (current version).

    Sends the full image directly to Mistral's vision model, which
    handles both title block localization and content extraction.

    Returns:
        JSON string of structured title block fields.
    """
    mistral_response = mistral.call_mistral_for_titleblock_extraction_from_image(image_path)
    return mistral_response


