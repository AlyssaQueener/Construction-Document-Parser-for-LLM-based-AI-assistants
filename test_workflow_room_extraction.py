import sys
import math
import cv2 as cv
import numpy as np

filename = 'examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf_page1.png'
# works with the png from alyssa but not with the one from soley using pymupdf (rebekka)

# Load image
src = cv.imread(filename, cv.IMREAD_GRAYSCALE)
if src is None:
    print("Failed to load image!")
    sys.exit()
h, w = src.shape

# Blur to reduce noise
blurred = cv.GaussianBlur(src, (5, 5), 0)

# Adaptive threshold
binary = cv.adaptiveThreshold(blurred, 255, cv.ADAPTIVE_THRESH_MEAN_C,
                              cv.THRESH_BINARY_INV, 15, 5)

# Stronger closing to connect walls
kernel = np.ones((5, 5), np.uint8)
closed = cv.morphologyEx(binary, cv.MORPH_CLOSE, kernel, iterations=2)

# HoughLinesP — tune parameters!
linesP = cv.HoughLinesP(closed, 1, np.pi / 180, 80, minLineLength=100, maxLineGap=10)

# Prepare blank canvas
lines_only_white = np.ones((h, w, 3), dtype=np.uint8) * 255

if linesP is not None:
    print(f"Detected {len(linesP)} lines")
    for l in linesP:
        x1, y1, x2, y2 = l[0]
        cv.line(lines_only_white, (x1, y1), (x2, y2), (0, 0, 255), 2, cv.LINE_AA)
else:
    print("no hough lines detected")

print("finished")

cv.imshow("Binary", binary)
cv.imshow("Closed", closed)
cv.imshow("Hough Lines Only (white bg)", lines_only_white)
cv.waitKey()
cv.destroyAllWindows()

