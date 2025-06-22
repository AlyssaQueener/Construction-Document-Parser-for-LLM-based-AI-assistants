import sys
import math
import cv2 as cv
import numpy as np

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

#[2] Preprocess the image ##################################################################
# a) Gaussian Blur 
# Blur to reduce noise
# Apply a Gaussian Blur to reduce noise (small variations in pixel values). This helps with later thresholding.
# Kernel size is set 5x5 -> 
blurred = cv.GaussianBlur(src, (5, 5), 0) 


# b)
# Adaptive threshold converts the image to black and white (binary), depending on the local neighborhood.
binary = cv.adaptiveThreshold(blurred, 255, cv.ADAPTIVE_THRESH_MEAN_C, #computes the mean of neighboring pixels
                              cv.THRESH_BINARY_INV, 21, 3) #inverts the binary result → walls/lines become white (255), background black (0).
                             # 15 = size of neighbourhood  # 5 = constant subtracted from mean 
# c) 
# Canny edges                                                
edges = cv.Canny(binary, 50,150)                                             

# Stronger closing to connect walls, Helps connect broken lines/walls by filling small gaps.
kernel = np.ones((3, 3), np.uint8)
edges_dilated = cv.dilate(edges, kernel, iterations=3)

# # HoughLinesP — tune parameters!
# linesP = cv.HoughLinesP(edges_dilated, 1, np.pi / 180, 80, minLineLength=15, maxLineGap=5)
# #1: resolution of rho (distance), 1 pixel.
# # np.pi/180: resolution of theta (angle), in radians.
# # 80: threshold — number of votes needed to accept a line.
# # minLineLength=100: ignore very short lines (<100 px).
# # maxLineGap=10: gaps of 10 px or less between line segments can be connected.
# # Returns a list of detected lines in the form [ [x1, y1, x2, y2], ... ].


# # Prepare blank canvas
# lines_only_white = np.ones((h, w, 3), dtype=np.uint8) * 255

# # if lines were detected how many ? 
# if linesP is not None:
#     print(f"Detected {len(linesP)} lines")
#     for l in linesP:
#         x1, y1, x2, y2 = l[0]
#         cv.line(lines_only_white, (x1, y1), (x2, y2), (0, 0, 255), 2, cv.LINE_AA)
# else:
#     print("no hough lines detected")

# print("finished")

kernel_big = np.ones((7, 7), np.uint8)
walls = cv.morphologyEx(edges_dilated, cv.MORPH_CLOSE, kernel_big)

# Optional: visualize the thickened "wall" image
cv.imshow("Walls (thickened)", walls)

# Now detect contours of walls
#This function finds contours (boundaries of connected components) in a binary image.
contours, hierarchy = cv.findContours(walls, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
# cv.RETR_EXTERNAL: This retrieval mode retrieves only the outermost contours. In the context of a floor plan, this means it will find the boundaries of the rooms and the outer perimeter of the building, without detecting contours of holes inside these shapes
# hierachy https://docs.opencv.org/4.x/d9/d8b/tutorial_py_contours_hierarchy.html
# Draw the detected wall contours
walls_contours = np.ones((h, w, 3), dtype=np.uint8) * 255
cv.drawContours(walls_contours, contours, -1, (0, 0, 0), thickness=cv.FILLED)

cv.imshow("Detected Wall Contours", walls_contours)
cv.imshow("Binary", binary)
cv.imshow("edges", edges)
#cv.imshow("Closed", closed)
#cv.imshow("Hough Lines Only (white bg)", lines_only_white)
cv.waitKey()
cv.destroyAllWindows()

