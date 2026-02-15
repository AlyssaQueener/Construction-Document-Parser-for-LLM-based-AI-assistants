"""
Floor Plan Parser for PDF Architectural Drawings

Extracts walls, doors, windows, and room boundaries from PDF floor plans using
geometric analysis and computer vision techniques.
"""

import fitz  # PyMuPDF
import json
import numpy as np
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import cv2
from scipy.spatial.distance import cdist
from collections import defaultdict
import matplotlib.pyplot as plt


class FloorPlanParser:
    """
    Parses architectural floor plan PDFs to extract rooms and structural elements.
    
    Attributes:
        pdf_path (str): Path to the PDF file
        walls (list): Detected wall line segments
        doors (list): Detected door line segments
        windows (list): Detected window line segments
        room_labels (list): Extracted text labels with positions
        rooms (dict): Detected room polygons with metadata
    """
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.page = self.doc[0]
        self.walls = []
        self.doors = []
        self.windows = []
        self.room_labels = []
        self.rooms = {}
        
    def extract_elements(self):
        """Extract walls, doors, windows, and text labels from PDF."""
        paths = self.page.get_drawings()
        text_dict = self.page.get_text("dict")
        
        for path in paths:
            self._classify_path(path)
            
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and len(text) > 2:
                            bbox = span["bbox"]
                            center_x = (bbox[0] + bbox[2]) / 2
                            center_y = (bbox[1] + bbox[3]) / 2
                            self.room_labels.append({
                                'text': text,
                                'center': (center_x, center_y),
                                'bbox': bbox
                            })
    
    def _classify_path(self, path):
        """
        Classify drawn paths as walls, doors, or windows.
        
        Classification based on stroke width and line length heuristics.
        """
        items = path.get("items", [])
        if not items:
            return
            
        lines = []
        for item in items:
            if item[0] == "l":
                x1, y1 = item[1]
                x2, y2 = item[2]
                lines.append(((x1, y1), (x2, y2)))
        
        stroke_width = path.get("width", 1)
        color = path.get("stroke", (0, 0, 0))
        
        if stroke_width > 2:
            self.walls.extend(lines)
        elif stroke_width < 1:
            for line in lines:
                length = self._line_length(line)
                if 20 < length < 100:
                    if self._is_likely_door(line):
                        self.doors.append(line)
                    else:
                        self.windows.append(line)
        else:
            self.walls.extend(lines)
    
    def _line_length(self, line):
        """Calculate Euclidean distance between line endpoints."""
        (x1, y1), (x2, y2) = line
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def _is_likely_door(self, line):
        """
        Heuristic door detection based on line length.
        
        Returns:
            bool: True if line length matches typical door dimensions
        """
        length = self._line_length(line)
        return 30 < length < 80
    
    def detect_rooms(self):
        """
        Detect room boundaries using contour-based approach.
        
        Creates a rasterized wall map, finds enclosed regions using contours,
        and matches them with text labels.
        
        Returns:
            dict: Room names mapped to polygon data
        """
        page_rect = self.page.rect
        width, height = int(page_rect.width), int(page_rect.height)
        
        img = np.zeros((height, width), dtype=np.uint8)
        
        for wall in self.walls:
            (x1, y1), (x2, y2) = wall
            cv2.line(img, (int(x1), int(y1)), (int(x2), int(y2)), 255, 3)
        
        img_inv = 255 - img
        contours, _ = cv2.findContours(img_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) > 1000:
                polygon_points = contour.reshape(-1, 2)
                if len(polygon_points) > 2:
                    polygon = Polygon(polygon_points)
                    
                    for label in self.room_labels:
                        point = Point(label['center'])
                        if polygon.contains(point):
                            self.rooms[label['text']] = {
                                'polygon': polygon,
                                'contour': contour,
                                'label_position': label['center'],
                                'area': cv2.contourArea(contour)
                            }
                            break
        
        return self.rooms
    
    def detect_rooms_advanced(self):
        """
        Advanced room detection using geometric line intersection analysis.
        
        Finds wall intersections and uses flood-fill approach to identify
        enclosed regions.
        
        Returns:
            dict: Room names mapped to polygon data
        """
        wall_lines = [LineString([p1, p2]) for p1, p2 in self.walls]
        
        intersections = []
        for i, line1 in enumerate(wall_lines):
            for j, line2 in enumerate(wall_lines[i+1:], i+1):
                if line1.intersects(line2):
                    intersection = line1.intersection(line2)
                    if hasattr(intersection, 'x'):
                        intersections.append((intersection.x, intersection.y))
        
        rooms = self._flood_fill_rooms(intersections, wall_lines)
        
        for label in self.room_labels:
            point = Point(label['center'])
            for i, room_polygon in enumerate(rooms):
                if room_polygon.contains(point):
                    self.rooms[label['text']] = {
                        'polygon': room_polygon,
                        'label_position': label['center'],
                        'area': room_polygon.area
                    }
        
        return self.rooms
    
    def _flood_fill_rooms(self, intersections, wall_lines):
        """
        Grid-based flood fill to identify enclosed room regions.
        
        Returns:
            list: Polygon objects representing detected rooms
        """
        rooms = []
        page_rect = self.page.rect
        grid_size = 10
        
        for x in range(0, int(page_rect.width), grid_size):
            for y in range(0, int(page_rect.height), grid_size):
                point = Point(x, y)
                
                if self._is_point_in_room(point, wall_lines):
                    room_polygon = self._expand_room_from_point(point, wall_lines)
                    if room_polygon and room_polygon.area > 1000:
                        rooms.append(room_polygon)
        
        return rooms
    
    def _is_point_in_room(self, point, wall_lines):
        """
        Ray casting algorithm to test if point is inside enclosed space.
        
        Returns:
            bool: True if point is inside a room
        """
        x, y = point.x, point.y
        crossings = 0
        
        for wall in wall_lines:
            coords = list(wall.coords)
            if len(coords) == 2:
                (x1, y1), (x2, y2) = coords
                if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
                    crossings += 1
        
        return crossings % 2 == 1
    
    def _expand_room_from_point(self, point, wall_lines):
        """
        Expand from seed point to find room boundaries.
        
        Note: Simplified implementation using circular buffer.
        Production version should use region growing algorithm.
        """
        return Point(point.x, point.y).buffer(50)
    
    def visualize_results(self):
        """Display extracted elements and detected rooms in matplotlib plots."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        
        ax1.set_title("Extracted Elements")
        
        for wall in self.walls:
            (x1, y1), (x2, y2) = wall
            ax1.plot([x1, x2], [y1, y2], 'k-', linewidth=2, 
                    label='Wall' if wall == self.walls[0] else "")
        
        for door in self.doors:
            (x1, y1), (x2, y2) = door
            ax1.plot([x1, x2], [y1, y2], 'b-', linewidth=3, 
                    label='Door' if door == self.doors[0] else "")
        
        for window in self.windows:
            (x1, y1), (x2, y2) = window
            ax1.plot([x1, x2], [y1, y2], 'g-', linewidth=3, 
                    label='Window' if window == self.windows[0] else "")
        
        for label in self.room_labels:
            ax1.plot(label['center'][0], label['center'][1], 'ro', markersize=8)
            ax1.text(label['center'][0], label['center'][1], label['text'], 
                    fontsize=8, ha='center', va='center')
        
        ax1.legend()
        ax1.invert_yaxis()
        ax1.set_aspect('equal')
        
        ax2.set_title("Detected Rooms")
        
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        for i, (room_name, room_data) in enumerate(self.rooms.items()):
            if 'polygon' in room_data:
                x, y = room_data['polygon'].exterior.xy
                ax2.fill(x, y, alpha=0.3, color=colors[i % len(colors)])
                ax2.plot(x, y, color=colors[i % len(colors)], linewidth=2)
                
                centroid = room_data['polygon'].centroid
                ax2.text(centroid.x, centroid.y, room_name, 
                        fontsize=10, ha='center', va='center', weight='bold')
        
        ax2.invert_yaxis()
        ax2.set_aspect('equal')
        
        plt.tight_layout()
        plt.show()
    
    def export_results(self, output_path):
        """
        Export detection results to JSON file.
        
        Args:
            output_path (str): Path for output JSON file
        """
        results = {
            'rooms': {},
            'walls': self.walls,
            'doors': self.doors,
            'windows': self.windows,
            'room_labels': self.room_labels
        }
        
        for room_name, room_data in self.rooms.items():
            results['rooms'][room_name] = {
                'area': room_data.get('area', 0),
                'label_position': room_data.get('label_position', [0, 0]),
                'polygon_bounds': list(room_data['polygon'].bounds) if 'polygon' in room_data else []
            }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)


def main():
    """
    Main execution pipeline for floor plan parsing.
    
    Steps:
    1. Extract structural elements from PDF
    2. Detect and segment rooms
    3. Visualize results
    4. Export to JSON
    """
    parser = FloorPlanParser("floorplan.pdf")
    
    print("Step 1: Extracting elements from PDF...")
    parser.extract_elements()
    print(f"Found {len(parser.walls)} walls, {len(parser.doors)} doors, {len(parser.windows)} windows")
    print(f"Found {len(parser.room_labels)} room labels: {[label['text'] for label in parser.room_labels]}")
    
    print("\nStep 2: Detecting rooms...")
    rooms = parser.detect_rooms()
    print(f"Detected {len(rooms)} rooms: {list(rooms.keys())}")
    
    print("\nStep 3: Visualizing results...")
    parser.visualize_results()
    
    print("\nStep 4: Exporting results...")
    parser.export_results("room_detection_results.json")
    
    return parser


if __name__ == "__main__":
    parser = main()