"""
PDF Floor Plan Data Extraction

Extracts line segments and text from architectural PDF floor plans, filters them,
and converts lines into closed polygons representing rooms and spaces.
"""

import os
import json
import math
import argparse
import fitz  # PyMuPDF
from shapely.geometry import LineString
from shapely.ops import polygonize


def extract_lines_and_text(pdf_path, min_length_pts=141.75):
    """
    Extract line segments and text elements from PDF.

    Args:
        pdf_path (str): Path to the PDF file
        min_length_pts (float): Minimum line length in PDF points (~5cm at 141.75)

    Returns:
        tuple: (lines, texts) where:
            - lines: List of dicts with 'start', 'end', 'length' keys
            - texts: List of dicts with 'text' and 'bbox' keys

    Raises:
        FileNotFoundError: If PDF file doesn't exist
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    all_lines = []
    all_texts = []

    for page in doc:
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    line_text = " ".join([span.get("text", "") for span in line.get("spans", [])]).strip()
                    bbox = line.get("bbox")
                    if line_text:
                        all_texts.append({"text": line_text, "bbox": bbox})

        for drawing in page.get_drawings():
            for item in drawing.get("items", []):
                if not item:
                    continue
                if item[0] == "l":
                    (x0, y0) = item[1]
                    (x1, y1) = item[2]
                    length = math.hypot(x1 - x0, y1 - y0)
                    if length >= min_length_pts:
                        all_lines.append({
                            "start": (round(x0, 2), round(y0, 2)),
                            "end": (round(x1, 2), round(y1, 2)),
                            "length": round(length, 2),
                        })

    doc.close()
    return all_lines, all_texts


def clean_lines(lines, min_length_pts=141.75):
    """
    Filter lines by minimum length threshold.

    Args:
        lines (list): List of line dicts with 'length' key
        min_length_pts (float): Minimum length in PDF points

    Returns:
        list: Filtered lines meeting length requirement
    """
    cleaned = [l for l in lines if l.get("length", 0) and l["length"] >= min_length_pts]
    return cleaned


def polygonize_lines(lines):
    """
    Convert line segments into closed polygons using Shapely.

    Uses Shapely's polygonize operation to find all closed regions
    formed by intersecting line segments.

    Args:
        lines (list): Line dicts with 'start' and 'end' coordinate tuples

    Returns:
        list: Polygons as lists of (x, y) coordinate tuples
    """
    line_strings = []
    for l in lines:
        s = l.get("start")
        e = l.get("end")
        if s and e and s != e:
            line_strings.append(LineString([s, e]))

    polygons = list(polygonize(line_strings))
    poly_coords = [list(poly.exterior.coords) for poly in polygons]
    return poly_coords


def save_json(output_path, data):
    """Save data to JSON file with UTF-8 encoding."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_cli():
    """
    Command-line interface for PDF floor plan extraction.

    Orchestrates the extraction, cleaning, and polygonization pipeline
    with configurable parameters and output options.
    """
    parser = argparse.ArgumentParser(description="Extract, clean and polygonize PDF floorplan data")
    parser.add_argument("pdf", help="Input PDF file path")
    parser.add_argument("-o", "--output", help="Output JSON file", default="floorplan_data.json")
    parser.add_argument("--min-length", type=float, default=141.75,
                        help="Minimum line length in PDF points (default ~141.75 pts = 5cm)")
    parser.add_argument("--save-intermediate", action="store_true",
                        help="Save intermediate lines/text JSON before polygonization")

    args = parser.parse_args()

    print(f"Extracting from: {args.pdf}")
    lines, texts = extract_lines_and_text(args.pdf, min_length_pts=args.min_length)
    print(f"Extracted {len(lines)} lines and {len(texts)} text elements (pre-cleaning)")

    cleaned = clean_lines(lines, min_length_pts=args.min_length)
    print(f"Kept {len(cleaned)} lines after cleaning (min_length={args.min_length})")

    polygons = polygonize_lines(cleaned)
    print(f"Polygonized into {len(polygons)} polygons")

    output = {
        "metadata": {
            "source_file": os.path.basename(args.pdf),
            "total_extracted_lines": len(lines),
            "total_cleaned_lines": len(cleaned),
            "total_texts": len(texts),
        },
        "lines": cleaned,
        "texts": texts,
        "polygons": polygons,
    }

    if args.save_intermediate:
        inter_path = os.path.splitext(args.output)[0] + "_intermediate.json"
        save_json(inter_path, {"lines": lines, "texts": texts})
        print(f"Saved intermediate JSON to {inter_path}")

    save_json(args.output, output)
    print(f"Saved final output to {args.output}")


if __name__ == "__main__":
    run_cli()