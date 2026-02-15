import fitz  # PyMuPDF
import json
from shapely.geometry import LineString
from shapely.ops import polygonize
import math

def extract_lines_and_text(pdf_path):
    doc = fitz.open(pdf_path)
    all_lines = []
    all_texts = []

    min_length_pts = 141.75  # 5 cm in points

    for page in doc:
        # Extract text
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = " ".join([span["text"] for span in line["spans"]])
                    bbox = line["bbox"]  # x0, y0, x1, y1
                    all_texts.append({"text": line_text, "bbox": bbox})

        # Extract drawing lines
        for item in page.get_drawings():
            for path in item["items"]:
                if path[0] == "l":  # 'l' = line
                    x0, y0 = path[1]
                    x1, y1 = path[2]
                    length = math.hypot(x1 - x0, y1 - y0)
                    if length >= min_length_pts:
                        all_lines.append(((x0, y0), (x1, y1)))

    return all_lines, all_texts

def group_lines_to_polygons(lines):
    line_strings = [LineString([start, end]) for start, end in lines]
    polygons = list(polygonize(line_strings))
    return polygons

# === RUN ===
pdf_path = "test4.pdf"  # <- replace with your file
lines, texts = extract_lines_and_text(pdf_path)
polygons = group_lines_to_polygons(lines)

# Save output
output = {
    "lines": lines,
    "texts": texts,
    "polygons": [list(poly.exterior.coords) for poly in polygons]
}

with open("floorplan_data.json", "w") as f:
    json.dump(output, f, indent=2)
