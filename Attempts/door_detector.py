import cv2
import numpy as np
import json
import os

# Parameters
floorplan_path = 'test4.png'
template_folder = 'templates'
output_image_path = 'detected_doors_norm8.png'
output_json_path = 'door_locations_norm8.json'
threshold = 0.7

# SCALING CORRECTION PARAMETERS - Adjust these based on your analysis
"""Door detector using OpenCV template matching.

This module searches a floorplan image for door templates and writes
normalized bounding boxes (0..1) in a JSON file compatible with downstream
tools that expect Mistral-style normalized coordinates.

Configuration is provided via top-level variables; consider converting
these to function parameters for reuse.
"""

import cv2
import numpy as np
import json
import os

# Configuration
floorplan_path = 'test4.png'
template_folder = 'templates'
output_image_path = 'detected_doors_norm8.png'
output_json_path = 'door_locations_norm8.json'
threshold = 0.7

# Scaling correction parameters (tweak if coordinates are offset)
SCALE_X = 1.0
SCALE_Y = 1.0
OFFSET_X = 0.0
OFFSET_Y = 0.0


# Load image
floorplan = cv2.imread(floorplan_path, cv2.IMREAD_GRAYSCALE)
if floorplan is None:
    raise SystemExit(f"Error: could not load image {floorplan_path}")

output_image = cv2.cvtColor(floorplan, cv2.COLOR_GRAY2BGR)
image_height, image_width = floorplan.shape

matches = []
seen = set()


def _normalize_and_store(pt, w, h, filename):
    """Convert a pixel detection to normalized Mistral-style bbox and return it.

    Returns a dict representing the match or None if invalid.
    """
    x_min_norm = pt[0] / image_width
    x_max_norm = (pt[0] + w) / image_width

    opencv_y_top = pt[1]
    opencv_y_bottom = pt[1] + h

    mistral_y_min = (image_height - opencv_y_bottom) / image_height
    mistral_y_max = (image_height - opencv_y_top) / image_height

    x_min_corrected = x_min_norm * SCALE_X + OFFSET_X
    x_max_corrected = x_max_norm * SCALE_X + OFFSET_X
    y_min_corrected = mistral_y_min * SCALE_Y + OFFSET_Y
    y_max_corrected = mistral_y_max * SCALE_Y + OFFSET_Y

    x_min_final = max(0.0, min(1.0, x_min_corrected))
    x_max_final = max(0.0, min(1.0, x_max_corrected))
    y_min_final = max(0.0, min(1.0, y_min_corrected))
    y_max_final = max(0.0, min(1.0, y_max_corrected))

    # Flip vertically/horizontally if needed (kept from original logic)
    flipped_y_min = 1.0 - y_max_final
    flipped_y_max = 1.0 - y_min_final
    y_min_final, y_max_final = flipped_y_min, flipped_y_max

    flipped_x_min = 1.0 - x_max_final
    flipped_x_max = 1.0 - x_min_final
    x_min_final, x_max_final = flipped_x_min, flipped_x_max

    if x_min_final >= x_max_final or y_min_final >= y_max_final:
        return None

    return {
        "template": filename,
        "bbox": {
            "x_min": round(x_min_final, 4),
            "y_min": round(y_min_final, 4),
            "x_max": round(x_max_final, 4),
            "y_max": round(y_max_final, 4),
        },
        "pixel_coordinates": {"x": int(pt[0]), "y": int(pt[1]), "width": int(w), "height": int(h)}
    }


# Template matching
if not os.path.exists(template_folder):
    raise SystemExit(f"Error: template folder '{template_folder}' not found")

template_files = [f for f in os.listdir(template_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
if not template_files:
    raise SystemExit(f"Error: no template images found in '{template_folder}'")

for filename in template_files:
    template_path = os.path.join(template_folder, filename)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"Warning: could not load template {filename}")
        continue

    w, h = template.shape[::-1]
    result = cv2.matchTemplate(floorplan, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)

    matches_for_template = 0
    for pt in zip(*locations[::-1]):
        key = (round(pt[0] / 10), round(pt[1] / 10))
        if key in seen:
            continue
        seen.add(key)

        top_left = pt
        bottom_right = (pt[0] + w, pt[1] + h)
        cv2.rectangle(output_image, top_left, bottom_right, (0, 0, 255), 2)

        record = _normalize_and_store(pt, w, h, filename)
        if record is None:
            print(f"Warning: invalid bbox for {filename}, skipping")
            continue
        matches.append(record)
        matches_for_template += 1

    print(f"Found {matches_for_template} matches for {filename}")


output_data = {
    "doors": matches,
    "image_dimensions": {"width": image_width, "height": image_height},
    "scaling_parameters": {"scale_x": SCALE_X, "scale_y": SCALE_Y, "offset_x": OFFSET_X, "offset_y": OFFSET_Y},
}

cv2.imwrite(output_image_path, output_image)
with open(output_json_path, 'w') as f:
    json.dump(output_data, f, indent=4)

print(f"\n[✓] {len(matches)} total matches from {len(template_files)} templates.")
print(f"[✓] Output image saved as '{output_image_path}'")
print(f"[✓] JSON data saved as '{output_json_path}'")


def suggest_scaling_parameters(opencv_json_path, mistral_json_path):
    """Suggest scale and offset to align OpenCV detections with Mistral boxes.

    Reads two JSON files (`opencv_json_path` from this detector and `mistral_json_path`
    produced by an AI detector) and computes scale factors and offsets to align
    average box sizes and centers.
    """
    try:
        with open(opencv_json_path, 'r') as f:
            opencv_data = json.load(f)
        with open(mistral_json_path, 'r') as f:
            mistral_data = json.load(f)

        opencv_boxes = [door['bbox'] for door in opencv_data.get('doors', [])]
        mistral_boxes = [room['bbox'] for room in mistral_data.get('rooms', [])]
        if not opencv_boxes or not mistral_boxes:
            print("Cannot suggest scaling: insufficient data in one or both files")
            return

        opencv_avg_w = np.mean([box['x_max'] - box['x_min'] for box in opencv_boxes])
        opencv_avg_h = np.mean([box['y_max'] - box['y_min'] for box in opencv_boxes])
        mistral_avg_w = np.mean([box['x_max'] - box['x_min'] for box in mistral_boxes])
        mistral_avg_h = np.mean([box['y_max'] - box['y_min'] for box in mistral_boxes])

        suggested_scale_x = mistral_avg_w / opencv_avg_w if opencv_avg_w > 0 else 1.0
        suggested_scale_y = mistral_avg_h / opencv_avg_h if opencv_avg_h > 0 else 1.0

        print(f"\nSuggested scaling parameters:")
        print(f"SCALE_X = {suggested_scale_x:.4f}")
        print(f"SCALE_Y = {suggested_scale_y:.4f}")

        opencv_center_x = np.mean([(box['x_min'] + box['x_max'])/2 for box in opencv_boxes])
        opencv_center_y = np.mean([(box['y_min'] + box['y_max'])/2 for box in opencv_boxes])
        mistral_center_x = np.mean([(box['x_min'] + box['x_max'])/2 for box in mistral_boxes])
        mistral_center_y = np.mean([(box['y_min'] + box['y_max'])/2 for box in mistral_boxes])

        suggested_offset_x = mistral_center_x - opencv_center_x * suggested_scale_x
        suggested_offset_y = mistral_center_y - opencv_center_y * suggested_scale_y

        print(f"OFFSET_X = {suggested_offset_x:.4f}")
        print(f"OFFSET_Y = {suggested_offset_y:.4f}")
    except Exception as e:
        print(f"Error analyzing scaling parameters: {e}")
        # Calculate average dimensions
        opencv_avg_w = np.mean([box['x_max'] - box['x_min'] for box in opencv_boxes])
        opencv_avg_h = np.mean([box['y_max'] - box['y_min'] for box in opencv_boxes])
        
        mistral_avg_w = np.mean([box['x_max'] - box['x_min'] for box in mistral_boxes])
        mistral_avg_h = np.mean([box['y_max'] - box['y_min'] for box in mistral_boxes])
        
        suggested_scale_x = mistral_avg_w / opencv_avg_w if opencv_avg_w > 0 else 1.0
        suggested_scale_y = mistral_avg_h / opencv_avg_h if opencv_avg_h > 0 else 1.0
        
        print(f"\nSuggested scaling parameters:")
        print(f"SCALE_X = {suggested_scale_x:.4f}")
        print(f"SCALE_Y = {suggested_scale_y:.4f}")
        
        # Calculate center offsets
        opencv_center_x = np.mean([(box['x_min'] + box['x_max'])/2 for box in opencv_boxes])
        opencv_center_y = np.mean([(box['y_min'] + box['y_max'])/2 for box in opencv_boxes])
        
        mistral_center_x = np.mean([(box['x_min'] + box['x_max'])/2 for box in mistral_boxes])
        mistral_center_y = np.mean([(box['y_min'] + box['y_max'])/2 for box in mistral_boxes])
        
        suggested_offset_x = mistral_center_x - opencv_center_x * suggested_scale_x
        suggested_offset_y = mistral_center_y - opencv_center_y * suggested_scale_y
        
        print(f"OFFSET_X = {suggested_offset_x:.4f}")
        print(f"OFFSET_Y = {suggested_offset_y:.4f}")
        
    except Exception as e:
        print(f"Error analyzing scaling parameters: {e}")

# Uncomment the following line and provide the path to your Mistral JSON to get scaling suggestions
# suggest_scaling_parameters(output_json_path, "path_to_mistral_output.json")