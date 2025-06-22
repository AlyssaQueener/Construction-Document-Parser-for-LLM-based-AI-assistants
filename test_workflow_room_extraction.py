import sys
import math
import cv2 as cv
import numpy as np
import pytesseract


filename = 'examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf_page1.png'
# works with the png from alyssa but not with the one from soley using pymupdf (rebekka)

#[1] Loading the image ##################################################################
# Load image Read the image in grayscale (single channel). 
# src will be a 2D NumPy array: each pixel is a value from 0 (black) to 255 (white).
src = cv.imread(filename, cv.IMREAD_GRAYSCALE)
if src is None:
    print("Failed to load image!")
    sys.exit()
h, w = src.shape # save height and width of the image for later 

# [2] Extract Textboxes and remove from image  ########################
extracted_text_data = [] 
# Perform OCR to get bounding box data
# lang='eng' (English) or 'deu' (German) or other as needed
data = pytesseract.image_to_data(src, output_type=pytesseract.Output.DICT, lang='deu', config='--psm 11') # Using 'deu' for German text

n_boxes = len(data['level'])
for i in range(n_boxes):
    text = data['text'][i].strip()
    conf = int(data['conf'][i])

    # Filter out empty text, low confidence, and perhaps very small or very large detected "words" if they're noise.
    # Level 5 is for words.
    if text and conf > 70 and data['level'][i] == 5: # Tune confidence (e.g., 60-80)
        x = data['left'][i]
        y = data['top'][i]
        w_text = data['width'][i]
        h_text = data['height'][i]

        extracted_text_data.append({
            'text': text,
            'confidence': conf,
            'bbox': {'x': x, 'y': y, 'width': w_text, 'height': h_text}
        })

print(f"Extracted Text Data: {extracted_text_data}")

# Create a copy of the original image to work on for wall processing.
# We'll remove text from this copy, then proceed with the rest of the pipeline.
# It's grayscale, so fill with 0 (black) or 255 (white)
img_for_wall_processing = src.copy()

# Draw black rectangles over detected text areas on the image used for wall processing.
# Assuming you want walls to be white later (THRESH_BINARY_INV), making text black
# will turn it into background, effectively removing it.
for item in extracted_text_data:
    bbox = item['bbox']
    x, y, w_text, h_text = bbox['x'], bbox['y'], bbox['width'], bbox['height']
    # Draw filled black rectangle (0) to remove text
    cv.rectangle(img_for_wall_processing, (x, y), (x + w_text, y + h_text), (255), -1)

#[2] Preprocess the image ##################################################################

#a) Gaussian Blur 
# Blur to reduce noise
# Apply a Gaussian Blur to reduce noise (small variations in pixel values). This helps with later thresholding.
# Kernel size is set 5x5 -> 
blurred = cv.GaussianBlur(img_for_wall_processing, (5, 5), 0) 

# b)
# Adaptive threshold converts the image to black and white (binary), depending on the local neighborhood.
binary = cv.adaptiveThreshold(blurred, 255, cv.ADAPTIVE_THRESH_MEAN_C, #computes the mean of neighboring pixels
                              cv.THRESH_BINARY_INV, 21, 3) #inverts the binary result → walls/lines become white (255), background black (0).
                             # 15 = size of neighbourhood  # 5 = constant subtracted from mean 


#c Remove furniture and other stuff 
# Find all connected components
num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(binary, connectivity=8)

# Create a blank image to draw filtered components on
# Create a blank image to draw filtered components on
filtered_binary = np.zeros_like(binary)

# Define all your thresholds BEFORE the loop for clarity and easier tuning
min_wall_area_keep = 500 # increase to remove short lines
max_wall_area_keep = (h * w) * 0.8
min_wall_aspect_ratio_thin_line = 3.0 # For very horizontal lines
max_wall_aspect_ratio_thin_line = 0.33   # For very vertical lines

min_furniture_area_discard = 10
max_furniture_area_discard = 8000
min_furniture_aspect_discard = 0.5
max_furniture_aspect_discard = 2.0

# Iterate through each component (label 0 is background)
for i in range(1, num_labels):
    area = stats[i, cv.CC_STAT_AREA]
    width = stats[i, cv.CC_STAT_WIDTH]
    height = stats[i, cv.CC_STAT_HEIGHT]
    aspect_ratio = float(width) / height
    if height == 0: aspect_ratio = 9999

    # Step 1: Assume it's NOT a wall initially
    is_wall_component = False

    # Step 2: Check if it matches "wall-like" criteria based on overall size and extreme aspect ratio
    # This filters for the main structural walls that are long and thin
    if (area > min_wall_area_keep and area < max_wall_area_keep):
        if (aspect_ratio > min_wall_aspect_ratio_thin_line or aspect_ratio < max_wall_aspect_ratio_thin_line):
            is_wall_component = True
    # OR if the component is just generally large enough to be a significant part of the structure
        elif area > (h * w) * 0.005: # Example: If area is > 0.5% of total image area, consider it. Tune this.
            is_wall_component = True

    # Step 3: Now, refine this by explicitly checking if it's "furniture-like" and thus should be excluded
    # This handles cases where furniture might accidentally meet some initial 'wall-like' area criteria,
    # but their aspect ratio marks them as furniture.
    if (area > min_furniture_area_discard and area < max_furniture_area_discard) and \
       (aspect_ratio >= min_furniture_aspect_discard and aspect_ratio <= max_furniture_aspect_discard):
        is_wall_component = False # If it's furniture, it's definitely NOT a wall component

    # Step 4: Include the component in filtered_binary only if it passed all checks
    if is_wall_component:
        filtered_binary[labels == i] = 255
# Apply a small morphological opening to clean up any remaining small noise or blobs
# This can help remove small curved items or remaining furniture dots
kernel_cleanup_small = np.ones((3, 3), np.uint8) # Adjust kernel size
cleaned_for_edges = cv.morphologyEx(filtered_binary, cv.MORPH_OPEN, kernel_cleanup_small)
# d) # Canny edges
# Now use binary_no_text for further processing (Canny, dilation, closing)
#edges = cv.Canny(binary_no_text, 50, 150)
edges = cv.Canny(cleaned_for_edges, 50, 150)
                         
                                                
# Stronger closing to connect walls, Helps connect broken lines/walls by filling small gaps.
kernel = np.ones((3, 3), np.uint8)
edges_dilated = cv.dilate(edges, kernel, iterations=3)

kernel_big = np.ones((31, 31), np.uint8)
walls = cv.morphologyEx(edges_dilated, cv.MORPH_CLOSE, kernel_big)

# cut outer sourundings (to remove rand)
# Define ROI coordinates (you'll need to tune these for your specific image)
x_min_roi = int(w * 0.15) # Example: 15% from left edge
y_min_roi = int(h * 0.25) # Example: 25% from top edge (to exclude top section)
x_max_roi = int(w * 0.85) # Example: 15% from right edge
y_max_roi = int(h * 0.75) # Example: 25% from bottom edge

# Create a black mask
mask = np.zeros_like(walls)

# Draw a white filled rectangle on the mask in the ROI
cv.rectangle(mask, (x_min_roi, y_min_roi), (x_max_roi, y_max_roi), 255, -1)

# Apply the mask to your 'walls' image
walls_roi = cv.bitwise_and(walls, mask)

# [4] Now detect contours for rooms ########################################################
# Use RETR_CCOMP for a two-level hierarchy: outer boundaries (rooms) and holes (fixtures/internal clutter)
contours_rooms, hierarchy_rooms = cv.findContours(walls_roi, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)

# room_contours = []
# if hierarchy_rooms is not None:
#     # Hierarchy structure: [Next, Previous, First_Child, Parent]
#     # For RETR_CCOMP, level 0 are outer contours (rooms), level 1 are holes (internal objects)
#     for i in range(len(contours_rooms)):
#         contour = contours_rooms[i]
#         area = cv.contourArea(contour)
#         # Filter out very small noise components
#         if area > 1000: # Tune this: min area for a valid room or significant internal feature
#             # Check if this contour has a parent (it's a hole) and its parent is level 0 (a room)
#             # Or if it's a top-level contour (a room) and not the overall image boundary
#             # hierarchy_rooms[0][i][3] == -1 means no parent (top level contour)
#             if hierarchy_rooms[0][i][3] == -1: # This is a top-level contour (could be a room or outer building boundary)
#                 # Filter out the very largest contour which is the overall building outline
#                 if area < (h * w * 0.7): # Assuming building is not 99% of image (adjust as needed)
#                     room_contours.append(contour)
#             elif hierarchy_rooms[0][i][3] != -1: # This contour has a parent (it's a hole)
#                 # This could be a room if its parent is the overall building, or internal clutter
#                 # For now, let's just consider top-level contours as rooms for simplicity
#                 # More sophisticated logic here could distinguish internal fixtures from rooms
#                 pass # We will primarily focus on outer contours as rooms for now


# # Draw the detected room contours
# rooms_output = np.ones((h, w, 3), dtype=np.uint8) * 255 # White background
# # Draw all identified room contours with a unique color or just black outlines
# for i, contour in enumerate(room_contours):
#     # You could assign different colors or just draw outlines
#     # color = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))
#     cv.drawContours(rooms_output, [contour], -1, (0, 0, 255), thickness=cv.FILLED) # Fill rooms in blue for clarity
#     # If you want outlines instead:
#     # cv.drawContours(rooms_output, [contour], -1, (0, 0, 0), thickness=2)

# cv.imshow("Detected Rooms", rooms_output) # The exciting result!





# Now detect contours of walls
#This function finds contours (boundaries of connected components) in a binary image.
contours, hierarchy = cv.findContours(walls_roi, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
# cv.RETR_EXTERNAL: This retrieval mode retrieves only the outermost contours. In the context of a floor plan, this means it will find the boundaries of the rooms and the outer perimeter of the building, without detecting contours of holes inside these shapes
# hierachy https://docs.opencv.org/4.x/d9/d8b/tutorial_py_contours_hierarchy.html
# Draw the detected wall contours
walls_contours = np.ones((h, w, 3), dtype=np.uint8) * 255

cv.drawContours(walls_contours, contours, -1, (0, 0, 0), thickness=cv.FILLED)
cv.imshow("Walls within ROI", walls_roi)
cv.imshow("Original Source", src)
cv.imshow("Image for Wall Processing (Text Removed)", img_for_wall_processing) # See text removed
cv.imshow("Binary (Text Removed)", filtered_binary)
cv.imshow("Edges (Text Removed)", edges)
cv.imshow("Walls (thickened)", walls)
cv.imshow("Detected Wall Contours (Filled)", walls_contours)

cv.waitKey() 
cv.destroyAllWindows()

