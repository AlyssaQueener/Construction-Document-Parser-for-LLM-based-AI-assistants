import cv2
import json

floorplan_path = "test4.png"
floorplan = cv2.imread(floorplan_path, cv2.IMREAD_GRAYSCALE)
image_height, image_width = floorplan.shape

# Save image dimensions to a JSON file
dimensions_json_path = "image_dimensions_opencv.json"
with open(dimensions_json_path, "w") as f:
    json.dump({"width": image_width, "height": image_height}, f, indent=4)

print(f"[✓] Image size saved: {image_width} x {image_height}")
