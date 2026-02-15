"""
Door Detection in Floor Plans using Template Matching

Detects doors in architectural floor plans using OpenCV template matching and converts
coordinates to normalized format compatible with Mistral AI coordinate system.
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

# Coordinate transformation parameters
SCALE_X = 1.0
SCALE_Y = 1.0
OFFSET_X = 0.0
OFFSET_Y = 0.0


def load_floorplan(path):
    """Load and validate floor plan image."""
    floorplan = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if floorplan is None:
        print(f"Error: Could not load image {path}")
        exit()
    return floorplan


def get_template_files(folder):
    """Get list of template image files from folder."""
    if not os.path.exists(folder):
        print(f"Error: Template folder '{folder}' not found")
        exit()
    
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        print(f"Error: No template images found in '{folder}'")
        exit()
    
    return files


def normalize_coordinates(pt, w, h, image_width, image_height):
    """
    Convert OpenCV pixel coordinates to normalized Mistral AI format.
    
    Transforms from OpenCV's top-left origin to Mistral's bottom-left origin,
    applies scaling corrections, and normalizes to [0,1] range.
    
    Args:
        pt: Top-left corner (x, y) in pixels
        w: Width in pixels
        h: Height in pixels
        image_width: Total image width
        image_height: Total image height
    
    Returns:
        dict: Normalized bounding box with x_min, y_min, x_max, y_max
    """
    # Normalize to [0,1]
    x_min_norm = pt[0] / image_width
    x_max_norm = (pt[0] + w) / image_width
    
    # Convert y-coordinates (OpenCV top-left to Mistral bottom-left)
    opencv_y_top = pt[1]
    opencv_y_bottom = pt[1] + h
    mistral_y_min = (image_height - opencv_y_bottom) / image_height
    mistral_y_max = (image_height - opencv_y_top) / image_height
    
    # Apply scaling corrections
    x_min_corrected = x_min_norm * SCALE_X + OFFSET_X
    x_max_corrected = x_max_norm * SCALE_X + OFFSET_X
    y_min_corrected = mistral_y_min * SCALE_Y + OFFSET_Y
    y_max_corrected = mistral_y_max * SCALE_Y + OFFSET_Y
    
    # Clamp to [0, 1]
    x_min_final = max(0.0, min(1.0, x_min_corrected))
    x_max_final = max(0.0, min(1.0, x_max_corrected))
    y_min_final = max(0.0, min(1.0, y_min_corrected))
    y_max_final = max(0.0, min(1.0, y_max_corrected))
    
    # Flip vertically and horizontally
    flipped_y_min = 1.0 - y_max_final
    flipped_y_max = 1.0 - y_min_final
    y_min_final, y_max_final = flipped_y_min, flipped_y_max
    
    flipped_x_min = 1.0 - x_max_final
    flipped_x_max = 1.0 - x_min_final
    x_min_final, x_max_final = flipped_x_min, flipped_x_max
    
    # Validate
    if x_min_final >= x_max_final or y_min_final >= y_max_final:
        return None
    
    return {
        "x_min": round(x_min_final, 4),
        "y_min": round(y_min_final, 4),
        "x_max": round(x_max_final, 4),
        "y_max": round(y_max_final, 4)
    }


def detect_doors(floorplan, template_folder, threshold):
    """
    Detect doors in floor plan using template matching.
    
    Args:
        floorplan: Grayscale floor plan image
        template_folder: Path to folder containing template images
        threshold: Matching threshold (0-1)
    
    Returns:
        tuple: (matches list, output_image with rectangles drawn)
    """
    output_image = cv2.cvtColor(floorplan, cv2.COLOR_GRAY2BGR)
    image_height, image_width = floorplan.shape
    
    matches = []
    seen = set()
    template_files = get_template_files(template_folder)
    
    print(f"Image dimensions: {image_width} x {image_height}")
    print(f"Found {len(template_files)} template files")
    
    for filename in template_files:
        template_path = os.path.join(template_folder, filename)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        
        if template is None:
            print(f"Warning: Could not load template {filename}")
            continue
        
        w, h = template.shape[::-1]
        print(f"Processing template {filename} (size: {w}x{h})")
        
        result = cv2.matchTemplate(floorplan, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        matches_for_template = 0
        for pt in zip(*locations[::-1]):
            # Deduplicate nearby detections
            key = (round(pt[0] / 10), round(pt[1] / 10))
            if key in seen:
                continue
            seen.add(key)
            
            # Draw detection rectangle
            top_left = pt
            bottom_right = (pt[0] + w, pt[1] + h)
            cv2.rectangle(output_image, top_left, bottom_right, (0, 0, 255), 2)
            
            # Normalize coordinates
            bbox = normalize_coordinates(pt, w, h, image_width, image_height)
            if bbox is None:
                print(f"Warning: Invalid bounding box for template {filename}, skipping")
                continue
            
            matches.append({
                "template": filename,
                "bbox": bbox,
                "pixel_coordinates": {
                    "x": int(pt[0]),
                    "y": int(pt[1]),
                    "width": int(w),
                    "height": int(h)
                }
            })
            matches_for_template += 1
        
        print(f"  Found {matches_for_template} matches for {filename}")
    
    return matches, output_image


def suggest_scaling_parameters(opencv_json_path, mistral_json_path):
    """
    Analyze JSON outputs to suggest optimal scaling parameters.
    
    Compares detected bounding boxes with ground truth to calculate
    appropriate SCALE_X, SCALE_Y, OFFSET_X, and OFFSET_Y values.
    """
    try:
        with open(opencv_json_path, 'r') as f:
            opencv_data = json.load(f)
        with open(mistral_json_path, 'r') as f:
            mistral_data = json.load(f)
        
        opencv_boxes = [door['bbox'] for door in opencv_data.get('doors', [])]
        mistral_boxes = [room['bbox'] for room in mistral_data.get('rooms', [])]
        
        if not opencv_boxes or not mistral_boxes:
            print("Cannot suggest scaling: insufficient data")
            return
        
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


def main():
    """Main execution function."""
    floorplan = load_floorplan(floorplan_path)
    matches, output_image = detect_doors(floorplan, template_folder, threshold)
    
    # Prepare output data
    image_height, image_width = floorplan.shape
    output_data = {
        "doors": matches,
        "image_dimensions": {
            "width": image_width,
            "height": image_height
        },
        "scaling_parameters": {
            "scale_x": SCALE_X,
            "scale_y": SCALE_Y,
            "offset_x": OFFSET_X,
            "offset_y": OFFSET_Y
        }
    }
    
    # Save results
    cv2.imwrite(output_image_path, output_image)
    with open(output_json_path, 'w') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"\n[✓] {len(matches)} total matches detected")
    print(f"[✓] Output image saved as '{output_image_path}'")
    print(f"[✓] JSON data saved as '{output_json_path}'")


if __name__ == "__main__":
    main()
    
   