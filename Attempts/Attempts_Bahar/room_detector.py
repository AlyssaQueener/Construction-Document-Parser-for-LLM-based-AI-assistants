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
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.page = self.doc[0]  # Assuming single page
        self.walls = []
        self.doors = []
        self.windows = []
        self.room_labels = []
        self.rooms = {}
        
    def extract_elements(self):
        """Extract all drawing elements from PDF"""
        # Get all paths (lines, rectangles, etc.)
        paths = self.page.get_drawings()
        
        # Get all text elements
        text_dict = self.page.get_text("dict")
        
        # Process paths to identify walls, doors, windows
        for path in paths:
            self._classify_path(path)
            
        # Extract room labels
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and len(text) > 2:  # Filter out single chars
                            bbox = span["bbox"]
                            center_x = (bbox[0] + bbox[2]) / 2
                            center_y = (bbox[1] + bbox[3]) / 2
                            self.room_labels.append({
                                'text': text,
                                'center': (center_x, center_y),
                                'bbox': bbox
                            })
    
    def _classify_path(self, path):
        """Classify path as wall, door, or window based on properties"""
        items = path.get("items", [])
        if not items:
            return
            
        # Extract line segments
        lines = []
        for item in items:
            if item[0] == "l":  # Line
                x1, y1 = item[1]
                x2, y2 = item[2]
                lines.append(((x1, y1), (x2, y2)))
        
        # Classify based on stroke width and color
        stroke_width = path.get("width", 1)
        color = path.get("stroke", (0, 0, 0))
        
        # Heuristic classification
        if stroke_width > 2:  # Thick lines are likely walls
            self.walls.extend(lines)
        elif stroke_width < 1:  # Thin lines might be doors/windows
            # Further classify based on length and position
            for line in lines:
                length = self._line_length(line)
                if 20 < length < 100:  # Door/window size range
                    if self._is_likely_door(line):
                        self.doors.append(line)
                    else:
                        self.windows.append(line)
        else:
            self.walls.extend(lines)
    
    def _line_length(self, line):
        """Calculate line length"""
        (x1, y1), (x2, y2) = line
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def _is_likely_door(self, line):
        """Heuristic to determine if line represents a door"""
        # This is a simplified heuristic - you might need to adjust
        length = self._line_length(line)
        return 30 < length < 80  # Typical door width range
    
    def detect_rooms(self):
        """Main room detection algorithm"""
        # Step 1: Create a raster representation
        page_rect = self.page.rect
        width, height = int(page_rect.width), int(page_rect.height)
        
        # Create binary image
        img = np.zeros((height, width), dtype=np.uint8)
        
        # Draw walls as white lines
        for wall in self.walls:
            (x1, y1), (x2, y2) = wall
            cv2.line(img, (int(x1), int(y1)), (int(x2), int(y2)), 255, 3)
        
        # Step 2: Find connected components (potential rooms)
        # Invert image so rooms are white, walls are black
        img_inv = 255 - img
        
        # Find contours
        contours, _ = cv2.findContours(img_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Step 3: Match room labels to contours
        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) > 1000:  # Filter small areas
                # Create polygon from contour
                polygon_points = contour.reshape(-1, 2)
                if len(polygon_points) > 2:
                    polygon = Polygon(polygon_points)
                    
                    # Find which room label is inside this polygon
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
        """Advanced room detection using line intersection analysis"""
        # Convert walls to line segments for geometric analysis
        wall_lines = [LineString([p1, p2]) for p1, p2 in self.walls]
        
        # Find intersections and create a graph
        intersections = []
        for i, line1 in enumerate(wall_lines):
            for j, line2 in enumerate(wall_lines[i+1:], i+1):
                if line1.intersects(line2):
                    intersection = line1.intersection(line2)
                    if hasattr(intersection, 'x'):  # Point intersection
                        intersections.append((intersection.x, intersection.y))
        
        # Use flood fill approach to find enclosed areas
        rooms = self._flood_fill_rooms(intersections, wall_lines)
        
        # Match with room labels
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
        """Use computational geometry to find enclosed rooms"""
        # This is a simplified version - real implementation would be more complex
        rooms = []
        
        # Create a grid-based approach for room detection
        page_rect = self.page.rect
        grid_size = 10
        
        for x in range(0, int(page_rect.width), grid_size):
            for y in range(0, int(page_rect.height), grid_size):
                point = Point(x, y)
                
                # Check if point is enclosed by walls
                if self._is_point_in_room(point, wall_lines):
                    # Expand from this point to find room boundaries
                    room_polygon = self._expand_room_from_point(point, wall_lines)
                    if room_polygon and room_polygon.area > 1000:
                        rooms.append(room_polygon)
        
        return rooms
    
    def _is_point_in_room(self, point, wall_lines):
        """Check if a point is inside an enclosed room"""
        # Ray casting algorithm simplified
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
        """Expand from a point to find room boundaries (simplified)"""
        # This is a placeholder for a more sophisticated algorithm
        # In practice, you'd use region growing or similar techniques
        return Point(point.x, point.y).buffer(50)  # Simplified circular room
    
    def visualize_results(self):
        """Visualize the detected rooms and elements"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        
        # Plot 1: Raw elements
        ax1.set_title("Extracted Elements")
        
        # Draw walls
        for wall in self.walls:
            (x1, y1), (x2, y2) = wall
            ax1.plot([x1, x2], [y1, y2], 'k-', linewidth=2, label='Wall' if wall == self.walls[0] else "")
        
        # Draw doors
        for door in self.doors:
            (x1, y1), (x2, y2) = door
            ax1.plot([x1, x2], [y1, y2], 'b-', linewidth=3, label='Door' if door == self.doors[0] else "")
        
        # Draw windows
        for window in self.windows:
            (x1, y1), (x2, y2) = window
            ax1.plot([x1, x2], [y1, y2], 'g-', linewidth=3, label='Window' if window == self.windows[0] else "")
        
        # Draw room labels
        for label in self.room_labels:
            ax1.plot(label['center'][0], label['center'][1], 'ro', markersize=8)
            ax1.text(label['center'][0], label['center'][1], label['text'], 
                    fontsize=8, ha='center', va='center')
        
        ax1.legend()
        ax1.invert_yaxis()  # PDF coordinates are inverted
        ax1.set_aspect('equal')
        
        # Plot 2: Detected rooms
        ax2.set_title("Detected Rooms")
        
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        for i, (room_name, room_data) in enumerate(self.rooms.items()):
            if 'polygon' in room_data:
                x, y = room_data['polygon'].exterior.xy
                ax2.fill(x, y, alpha=0.3, color=colors[i % len(colors)])
                ax2.plot(x, y, color=colors[i % len(colors)], linewidth=2)
                
                # Add room label
                centroid = room_data['polygon'].centroid
                ax2.text(centroid.x, centroid.y, room_name, 
                        fontsize=10, ha='center', va='center', weight='bold')
        
        ax2.invert_yaxis()
        ax2.set_aspect('equal')
        
        plt.tight_layout()
        plt.show()
    
    def export_results(self, output_path):
        """Export results to JSON"""
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

# Usage example
def main():
    # Initialize parser
    parser = FloorPlanParser("floorplan.pdf")
    
    # Step 1: Extract all elements from PDF
    print("Step 1: Extracting elements from PDF...")
    parser.extract_elements()
    print(f"Found {len(parser.walls)} walls, {len(parser.doors)} doors, {len(parser.windows)} windows")
    print(f"Found {len(parser.room_labels)} room labels: {[label['text'] for label in parser.room_labels]}")
    
    # Step 2: Detect rooms
    print("\nStep 2: Detecting rooms...")
    rooms = parser.detect_rooms()
    print(f"Detected {len(rooms)} rooms: {list(rooms.keys())}")
    
    # Step 3: Visualize results
    print("\nStep 3: Visualizing results...")
    parser.visualize_results()
    
    # Step 4: Export results
    print("\nStep 4: Exporting results...")
    parser.export_results("room_detection_results.json")
    
    return parser

if __name__ == "__main__":
    # Make sure you have these libraries installed:
    # pip install PyMuPDF shapely opencv-python scipy matplotlib numpy
    
    parser = main()