# SIMPLE FLOORPLAN PDF TO JSON CONVERTER
# This code extracts lines and text from a PDF floorplan and saves to JSON

import fitz  # PyMuPDF library
import json

def extract_floorplan_to_json(pdf_path, output_json="floorplan_data1.json"):
    """
    Main function: Extract floorplan data from PDF and save to JSON
    
    STEP-BY-STEP EXPLANATION:
    
    STEP 1: Open the PDF file
    - We use fitz.open() to load the PDF
    - Check if the file exists and can be opened
    """
    print("🏠 FLOORPLAN PDF TO JSON CONVERTER")
    print("=" * 50)
    
    # STEP 1: Open PDF file
    print(f"📂 STEP 1: Opening PDF file...")
    print(f"   File path: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        print(f"   ✅ PDF opened successfully!")
        print(f"   📄 Total pages: {len(doc)}")
    except Exception as e:
        print(f"   ❌ Error: Could not open PDF file")
        print(f"   💡 Make sure the file path is correct and file exists")
        return None
    
    # STEP 2: Get the first page
    print(f"\n🔍 STEP 2: Analyzing first page...")
    page = doc[0]  # Most floorplans are single page
    page_width = page.rect.width
    page_height = page.rect.height
    print(f"   📏 Page dimensions: {page_width:.1f} x {page_height:.1f} points")
    print(f"   💡 1 point = 1/72 inch, so this is roughly {page_width/72:.1f}\" x {page_height/72:.1f}\"")
    
    """
    STEP 3: Extract all drawing elements (lines)
    - get_drawings() returns all vector graphics in the PDF
    - These include walls, doors, windows, and other architectural elements
    - Each drawing contains "items" which are individual line segments
    """
    print(f"\n📐 STEP 3: Extracting lines (walls, doors, windows)...")
    
    drawings = page.get_drawings()
    print(f"   🔍 Found {len(drawings)} drawing objects")
    
    lines = []
    line_count = 0
    
    # Loop through each drawing object
    for drawing_index, drawing in enumerate(drawings):
        # Each drawing can contain multiple items (line segments)
        for item in drawing["items"]:
            if item[0] == "l":  # "l" means this is a line segment
                # Extract start and end points
                start_point = item[1]  # Point(x1, y1)
                end_point = item[2]    # Point(x2, y2)
                
                # Calculate line length using Pythagorean theorem
                length = ((end_point.x - start_point.x)**2 + (end_point.y - start_point.y)**2)**0.5
                
                # Store line data
                lines.append({
                    "id": line_count,
                    "drawing_group": drawing_index,
                    "start_x": round(start_point.x, 2),
                    "start_y": round(start_point.y, 2),
                    "end_x": round(end_point.x, 2),
                    "end_y": round(end_point.y, 2),
                    "length": round(length, 2)
                })
                line_count += 1
    
    print(f"   ✅ Extracted {len(lines)} line segments")
    print(f"   📊 These represent walls, doors, windows, and other elements")
    
    """
    STEP 4: Extract all text elements
    - get_text("dict") returns text with detailed positioning information
    - This includes room names, labels, dimensions, etc.
    - We get the exact position, size, and font information for each text
    """
    print(f"\n📝 STEP 4: Extracting text (room names, labels)...")
    
    text_dict = page.get_text("dict")
    texts = []
    text_count = 0
    
    # Navigate through the text structure
    for block in text_dict["blocks"]:
        if "lines" in block:  # This is a text block (not an image)
            for line in block["lines"]:
                for span in line["spans"]:
                    text_content = span["text"].strip()
                    
                    # Only keep non-empty text
                    if text_content:
                        texts.append({
                            "id": text_count,
                            "text": text_content,
                            "x": round(span["bbox"][0], 2),  # Left position
                            "y": round(span["bbox"][1], 2),  # Top position
                            "width": round(span["bbox"][2] - span["bbox"][0], 2),
                            "height": round(span["bbox"][3] - span["bbox"][1], 2),
                            "font_size": round(span["size"], 1),
                            "font_name": span["font"]
                        })
                        text_count += 1
    
    print(f"   ✅ Extracted {len(texts)} text elements")
    
    # Show some example text found
    print(f"   📋 Sample text found:")
    for i, text in enumerate(texts[:5]):  # Show first 5 texts
        print(f"      {i+1}. '{text['text']}' at ({text['x']}, {text['y']})")
    
    """
    STEP 5: Analyze the data
    - Identify potential room names (longer text that looks like room names)
    - Calculate statistics about lines and text
    - Prepare organized data structure
    """
    print(f"\n🧮 STEP 5: Analyzing extracted data...")
    
    # Find potential room names (text that looks like room labels)
    potential_rooms = []
    for text in texts:
        # Room names are usually:
        # - More than 2 characters
        # - Contain letters (not just numbers)
        # - Not too long (not paragraphs)
        if (len(text['text']) > 2 and 
            len(text['text']) < 30 and 
            any(c.isalpha() for c in text['text'])):
            potential_rooms.append(text['text'])
    
    print(f"   🏠 Found {len(potential_rooms)} potential room names:")
    for room in potential_rooms[:10]:  # Show first 10
        print(f"      - {room}")
    
    # Calculate line statistics
    if lines:
        line_lengths = [line['length'] for line in lines]
        line_stats = {
            "shortest": round(min(line_lengths), 2),
            "longest": round(max(line_lengths), 2),
            "average": round(sum(line_lengths) / len(line_lengths), 2),
            "total_lines": len(lines)
        }
    else:
        line_stats = {"total_lines": 0}
    
    print(f"   📏 Line statistics: {line_stats}")
    
    """
    STEP 6: Create final JSON structure
    - Organize all data into a clear, structured format
    - Include metadata about the page and analysis
    - Make it easy to use for further processing
    """
    print(f"\n📦 STEP 6: Creating JSON data structure...")
    
    floorplan_data = {
        "metadata": {
            "source_file": pdf_path,
            "page_dimensions": {
                "width": page_width,
                "height": page_height,
                "width_inches": round(page_width/72, 2),
                "height_inches": round(page_height/72, 2)
            },
            "extraction_summary": {
                "total_lines": len(lines),
                "total_text_elements": len(texts),
                "potential_room_count": len(potential_rooms)
            }
        },
        "lines": lines,
        "text_elements": texts,
        "analysis": {
            "potential_room_names": potential_rooms,
            "line_statistics": line_stats,
            "font_sizes_found": list(set([text['font_size'] for text in texts])),
            "coordinate_bounds": {
                "min_x": min([line['start_x'] for line in lines] + [line['end_x'] for line in lines]) if lines else 0,
                "max_x": max([line['start_x'] for line in lines] + [line['end_x'] for line in lines]) if lines else 0,
                "min_y": min([line['start_y'] for line in lines] + [line['end_y'] for line in lines]) if lines else 0,
                "max_y": max([line['start_y'] for line in lines] + [line['end_y'] for line in lines]) if lines else 0
            }
        }
    }
    
    """
    STEP 7: Save to JSON file
    - Write the structured data to a JSON file
    - Use proper formatting for readability
    - Handle any file writing errors
    """
    print(f"\n💾 STEP 7: Saving to JSON file...")
    print(f"   📄 Output file: {output_json}")
    
    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(floorplan_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ JSON file created successfully!")
        print(f"   📊 File contains:")
        print(f"      - {len(lines)} lines (walls, doors, windows)")
        print(f"      - {len(texts)} text elements")
        print(f"      - {len(potential_rooms)} potential room names")
        print(f"      - Complete coordinate and size information")
        
    except Exception as e:
        print(f"   ❌ Error saving JSON file: {e}")
        return None
    
    # Close the PDF
    doc.close()
    
    print(f"\n🎉 CONVERSION COMPLETE!")
    print(f"Your floorplan data is now saved in '{output_json}'")
    
    return floorplan_data

# MAIN EXECUTION
if __name__ == "__main__":
    # Your PDF file path
    pdf_file = "C:\\Users\\HP\\Desktop\\softwareLab\\input\\test4.pdf"
    
    # Output JSON file name
    output_file = "floorplan_data1.json"
    
    # Run the conversion
    result = extract_floorplan_to_json(pdf_file, output_file)
    
    if result:
        print(f"\n📋 QUICK SUMMARY:")
        print(f"   📁 Input: {pdf_file}")
        print(f"   📄 Output: {output_file}")
        print(f"   📐 Lines extracted: {len(result['lines'])}")
        print(f"   📝 Text elements: {len(result['text_elements'])}")
        print(f"   🏠 Potential rooms: {len(result['analysis']['potential_room_names'])}")
        
        # Show first few room names found
        if result['analysis']['potential_room_names']:
            print(f"   🏠 Room names found: {', '.join(result['analysis']['potential_room_names'][:5])}")
    else:
        print(f"\n❌ Conversion failed. Please check the file path and try again.")