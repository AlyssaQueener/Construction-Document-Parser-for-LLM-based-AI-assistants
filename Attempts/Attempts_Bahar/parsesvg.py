import xml.etree.ElementTree as ET
import re
import json
from typing import Dict, List, Any, Optional, Tuple

class SVGFloorPlanParser:
    def __init__(self):
        self.namespaces = {
            'svg': 'http://www.w3.org/2000/svg',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
    
    def parse_svg_file(self, file_path: str) -> Dict[str, Any]:
        """Parse an SVG file and extract floor plan elements"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self.parse_svg_element(root)
        except ET.ParseError as e:
            raise ValueError(f"Invalid SVG file: {e}")
    
    def parse_svg_string(self, svg_content: str) -> Dict[str, Any]:
        """Parse SVG content from string"""
        try:
            root = ET.fromstring(svg_content)
            return self.parse_svg_element(root)
        except ET.ParseError as e:
            raise ValueError(f"Invalid SVG content: {e}")
    
    def parse_svg_element(self, root: ET.Element) -> Dict[str, Any]:
        """Extract all relevant elements from SVG root"""
        result = {
            "rectangles": [],
            "circles": [],
            "polygons": [],
            "lines": [],
            "text": [],
            "paths": [],
            "groups": [],
            "viewbox": self._get_viewbox(root),
            "dimensions": self._get_dimensions(root)
        }
        
        # Process all elements recursively
        self._process_elements(root, result)
        
        return result
    
    def _process_elements(self, element: ET.Element, result: Dict[str, Any], transform: str = ""):
        """Recursively process all SVG elements"""
        # Get transform for this element
        current_transform = element.get('transform', '')
        if transform and current_transform:
            full_transform = f"{transform} {current_transform}"
        else:
            full_transform = transform or current_transform
        
        # Process based on element type
        tag = element.tag.lower()
        if tag.endswith('rect') or tag == 'rect':
            self._parse_rectangle(element, result, full_transform)
        elif tag.endswith('circle') or tag == 'circle':
            self._parse_circle(element, result, full_transform)
        elif tag.endswith('polygon') or tag == 'polygon':
            self._parse_polygon(element, result, full_transform)
        elif tag.endswith('line') or tag == 'line':
            self._parse_line(element, result, full_transform)
        elif tag.endswith('text') or tag == 'text':
            self._parse_text(element, result, full_transform)
        elif tag.endswith('path') or tag == 'path':
            self._parse_path(element, result, full_transform)
        elif tag.endswith('g') or tag == 'g':
            self._parse_group(element, result, full_transform)
        
        # Process child elements
        for child in element:
            self._process_elements(child, result, full_transform)
    
    def _parse_rectangle(self, element: ET.Element, result: Dict[str, Any], transform: str):
        """Parse rectangle element"""
        rect = {
            "x": float(element.get('x', 0)),
            "y": float(element.get('y', 0)),
            "width": float(element.get('width', 0)),
            "height": float(element.get('height', 0)),
            "style": element.get('style', ''),
            "class": element.get('class', ''),
            "id": element.get('id', ''),
            "fill": element.get('fill', ''),
            "stroke": element.get('stroke', ''),
            "stroke_width": element.get('stroke-width', ''),
            "transform": transform
        }
        result["rectangles"].append(rect)
    
    def _parse_circle(self, element: ET.Element, result: Dict[str, Any], transform: str):
        """Parse circle element"""
        circle = {
            "cx": float(element.get('cx', 0)),
            "cy": float(element.get('cy', 0)),
            "r": float(element.get('r', 0)),
            "style": element.get('style', ''),
            "class": element.get('class', ''),
            "id": element.get('id', ''),
            "fill": element.get('fill', ''),
            "stroke": element.get('stroke', ''),
            "stroke_width": element.get('stroke-width', ''),
            "transform": transform
        }
        result["circles"].append(circle)
    
    def _parse_polygon(self, element: ET.Element, result: Dict[str, Any], transform: str):
        """Parse polygon element"""
        points_str = element.get('points', '')
        points = self._parse_points(points_str)
        
        polygon = {
            "points": points,
            "style": element.get('style', ''),
            "class": element.get('class', ''),
            "id": element.get('id', ''),
            "fill": element.get('fill', ''),
            "stroke": element.get('stroke', ''),
            "stroke_width": element.get('stroke-width', ''),
            "transform": transform
        }
        result["polygons"].append(polygon)
    
    def _parse_line(self, element: ET.Element, result: Dict[str, Any], transform: str):
        """Parse line element"""
        line = {
            "x1": float(element.get('x1', 0)),
            "y1": float(element.get('y1', 0)),
            "x2": float(element.get('x2', 0)),
            "y2": float(element.get('y2', 0)),
            "style": element.get('style', ''),
            "class": element.get('class', ''),
            "id": element.get('id', ''),
            "stroke": element.get('stroke', ''),
            "stroke_width": element.get('stroke-width', ''),
            "transform": transform
        }
        result["lines"].append(line)
    
    def _parse_text(self, element: ET.Element, result: Dict[str, Any], transform: str):
        """Parse text element"""
        # Get text content
        text_content = element.text or ''
        for child in element:
            if child.text:
                text_content += child.text
            if child.tail:
                text_content += child.tail
        
        # Parse font-size from style or direct attribute
        font_size = self._extract_font_size(element)
        
        text = {
            "text": text_content.strip(),
            "position": [
                float(element.get('x', 0)),
                float(element.get('y', 0))
            ],
            "font_size": font_size,
            "style": element.get('style', ''),
            "class": element.get('class', ''),
            "id": element.get('id', ''),
            "fill": element.get('fill', ''),
            "font_family": element.get('font-family', ''),
            "text_anchor": element.get('text-anchor', ''),
            "transform": transform
        }
        result["text"].append(text)
    
    def _parse_path(self, element: ET.Element, result: Dict[str, Any], transform: str):
        """Parse path element"""
        path = {
            "d": element.get('d', ''),
            "style": element.get('style', ''),
            "class": element.get('class', ''),
            "id": element.get('id', ''),
            "fill": element.get('fill', ''),
            "stroke": element.get('stroke', ''),
            "stroke_width": element.get('stroke-width', ''),
            "transform": transform
        }
        result["paths"].append(path)
    
    def _parse_group(self, element: ET.Element, result: Dict[str, Any], transform: str):
        """Parse group element"""
        group = {
            "id": element.get('id', ''),
            "class": element.get('class', ''),
            "style": element.get('style', ''),
            "transform": transform
        }
        result["groups"].append(group)
    
    def _parse_points(self, points_str: str) -> List[Tuple[float, float]]:
        """Parse points string into list of coordinate tuples"""
        points = []
        if not points_str:
            return points
        
        # Clean up the points string
        points_str = re.sub(r'[,\s]+', ' ', points_str.strip())
        coords = points_str.split()
        
        # Group coordinates in pairs
        for i in range(0, len(coords), 2):
            if i + 1 < len(coords):
                try:
                    x = float(coords[i])
                    y = float(coords[i + 1])
                    points.append((x, y))
                except ValueError:
                    continue
        
        return points
    
    def _extract_font_size(self, element: ET.Element) -> float:
        """Extract font size from element"""
        # Check direct attribute first
        font_size = element.get('font-size')
        if font_size:
            return self._parse_font_size(font_size)
        
        # Check style attribute
        style = element.get('style', '')
        if style:
            # Look for font-size in style
            match = re.search(r'font-size:\s*([^;]+)', style)
            if match:
                return self._parse_font_size(match.group(1))
        
        return 12.0  # Default font size
    
    def _parse_font_size(self, font_size_str: str) -> float:
        """Parse font size string to float"""
        try:
            # Remove units like 'px', 'pt', 'em', etc.
            font_size_str = re.sub(r'[a-zA-Z%]+', '', font_size_str.strip())
            return float(font_size_str)
        except ValueError:
            return 12.0
    
    def _get_viewbox(self, root: ET.Element) -> Optional[Dict[str, float]]:
        """Extract viewBox information"""
        viewbox = root.get('viewBox')
        if viewbox:
            try:
                values = [float(x) for x in viewbox.split()]
                if len(values) == 4:
                    return {
                        "x": values[0],
                        "y": values[1],
                        "width": values[2],
                        "height": values[3]
                    }
            except ValueError:
                pass
        return None
    
    def _get_dimensions(self, root: ET.Element) -> Dict[str, Optional[str]]:
        """Extract width and height from root element"""
        return {
            "width": root.get('width'),
            "height": root.get('height')
        }


# Example usage
def main():
    parser = SVGFloorPlanParser()
    
    # OPTION 1: Direct file path - Change this to your SVG file path
    file_path = "floorplan.svg"  # ← CHANGE THIS PATH
    output_json = "floorplan_parsed1.json"  # ← OUTPUT JSON FILE NAME
    
    try:
        result = parser.parse_svg_file(file_path)
        
        # Save to JSON file
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print(f"✓ Parsed SVG successfully!")
        print(f"✓ JSON saved to: {output_json}")
        print(f"✓ Found {len(result['rectangles'])} rectangles")
        print(f"✓ Found {len(result['text'])} text elements")
        print(f"✓ Found {len(result['circles'])} circles")
        print(f"✓ Found {len(result['lines'])} lines")
        
        # Still print to console if you want to see it
        print("\nPreview (first 50 lines):")
        json_str = json.dumps(result, indent=2)
        lines = json_str.split('\n')
        for i, line in enumerate(lines[:50]):
            print(line)
        if len(lines) > 50:
            print(f"... and {len(lines) - 50} more lines")
            
    except Exception as e:
        print(f"Error parsing SVG file: {e}")
    
    # OPTION 2: Direct SVG content - Replace with your SVG content
    # your_svg_content = '''
    # <svg>...</svg>
    # '''
    # result = parser.parse_svg_string(your_svg_content)
    # 
    # # Save to JSON
    # with open("parsed_svg.json", 'w', encoding='utf-8') as f:
    #     json.dump(result, f, indent=2)
    # print("JSON saved to parsed_svg.json")


def main_interactive():
    """Interactive version with menu"""
    parser = SVGFloorPlanParser()
    
    print("SVG Floor Plan Parser")
    print("====================")
    
    while True:
        print("\nOptions:")
        print("1. Parse SVG from file")
        print("2. Parse SVG from text input")
        print("3. Use example SVG")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            file_path = input("Enter the path to your SVG file: ").strip()
            output_file = input("Enter output JSON filename (or press Enter for 'output.json'): ").strip()
            if not output_file:
                output_file = "output.json"
            
            try:
                result = parser.parse_svg_file(file_path)
                
                # Save to JSON file
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                print(f"\n✓ Parsed SVG successfully!")
                print(f"✓ JSON saved to: {output_file}")
                print(f"✓ Found {len(result['rectangles'])} rectangles")
                print(f"✓ Found {len(result['text'])} text elements")
                print(f"✓ Found {len(result['circles'])} circles")
                print(f"✓ Found {len(result['lines'])} lines")
                
            except Exception as e:
                print(f"Error parsing SVG file: {e}")
        
        elif choice == '2':
            print("\nPaste your SVG content (press Enter twice when done):")
            svg_lines = []
            while True:
                line = input()
                if line == "" and len(svg_lines) > 0 and svg_lines[-1] == "":
                    break
                svg_lines.append(line)
            
            svg_content = '\n'.join(svg_lines[:-1])  # Remove the last empty line
            
            if svg_content.strip():
                output_file = input("Enter output JSON filename (or press Enter for 'output.json'): ").strip()
                if not output_file:
                    output_file = "output.json"
                
                try:
                    result = parser.parse_svg_string(svg_content)
                    
                    # Save to JSON file
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2)
                    
                    print(f"\n✓ Parsed SVG successfully!")
                    print(f"✓ JSON saved to: {output_file}")
                    print(f"✓ Found {len(result['rectangles'])} rectangles")
                    print(f"✓ Found {len(result['text'])} text elements")
                    print(f"✓ Found {len(result['circles'])} circles")
                    print(f"✓ Found {len(result['lines'])} lines")
                    
                except Exception as e:
                    print(f"Error parsing SVG content: {e}")
            else:
                print("No SVG content provided.")
        
        elif choice == '3':
            # Example SVG content for testing
            example_svg = '''<?xml version="1.0" encoding="UTF-8"?>
            <svg width="400" height="300" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
                <rect x="100" y="100" width="200" height="150" fill="none" stroke="black" stroke-width="2" id="room1"/>
                <rect x="120" y="120" width="50" height="30" fill="brown" id="table"/>
                <circle cx="200" cy="80" r="20" fill="lightblue" id="light"/>
                <line x1="100" y1="175" x2="300" y2="175" stroke="red" stroke-width="1"/>
                <text x="200" y="180" font-size="16" text-anchor="middle" fill="black">Kitchen</text>
                <polygon points="50,50 80,50 65,20" fill="green" id="arrow"/>
            </svg>'''
            
            try:
                result = parser.parse_svg_string(example_svg)
                
                # Save example to JSON
                output_file = "example_parsed.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                print(f"\n✓ Parsed example SVG successfully!")
                print(f"✓ JSON saved to: {output_file}")
                print(f"✓ Found {len(result['rectangles'])} rectangles")
                print(f"✓ Found {len(result['text'])} text elements")
                print(f"✓ Found {len(result['circles'])} circles")
                print(f"✓ Found {len(result['lines'])} lines")
                
            except Exception as e:
                print(f"Error parsing example SVG: {e}")
        
        elif choice == '4':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    # Choose which version to run:
    
    # Option A: Direct file parsing (no user input)
    main()
    
    # Option B: Interactive menu (uncomment to use)
    # main_interactive()