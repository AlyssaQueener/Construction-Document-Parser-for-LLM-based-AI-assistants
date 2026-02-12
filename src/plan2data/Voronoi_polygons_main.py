from Voronoi_polygons_functions import *

if __name__=="__main__":
    # Change to the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    os.chdir(project_root)
    #pdf_path = "examples/FloorplansAndSectionViews/bemasster-grundriss-plankopf.pdf"
    #pdf_path= "examples/FloorplansAndSectionViews/BasicTestPlan.pdf"
    #pdf_path = "examples/FloorplansAndSectionViews/GrundrissEG_2022_web.pdf"
    #pdf_path = "examples/FloorplansAndSectionViews/2d-grundriss-wohnflaeche.pdf"
    #pdf_path = "examples/FloorplansAndSectionViews/GrundrissEG_2022_web.pdf"
    #pdf_path = "examples/FloorplansAndSectionViews/modern-stilt-house.pdf"
    pdf_path = "src/validation/Floorplan/titleblock/testdata/floorplan-test-1.pdf"

    #pdf_path = "examples/FloorplansAndSectionViews/Simple Floorplan/04_Simple.pdf"
    neighboring_rooms_voronoi(pdf_path)

    # NAMING convention of output files 
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    json_path = f'output/Floorplan/Voronoi/Neighboring rooms/neighbouring_rooms_{filename}.json'
    output_filename= f'output/Floorplan/Voronoi/Textbboxes_rooms/textbboxes_rooms_{filename}.json'
    output_PDF = f'output/Floorplan/Voronoi/PDF_Area_clipped/clipped_filltered_{filename}.pdf'
    output_centerpoints =  f'output/Floorplan/Voronoi/Centerpoints_Rooms/centerpoints_rooms_{filename}.json'
    
    doc = fitz.open(pdf_path)

    page = doc[0]
    # clip rectangle to exclude plan information -> using fitz.Rect(x0, y0, x1, y1) where x0,yo is top left corner and x1,y1 is bottom right corner
    width,height = page.rect.width, page.rect.height
    clip_rect = fitz.Rect(0, 0, width * 0.72, height * 0.8)
    flipped_rect =(
        clip_rect.x0,                    # x_min stays the same
        height - clip_rect.y1,           # y_min (flip the bottom of clip_rect)
        clip_rect.x1,                    # x_max stays the same
        height - clip_rect.y0            # y_max (flip the top of clip_rect)
    )
    page.add_rect_annot(clip_rect)

    # Save to a debug file
    doc.save("clipped_debug.pdf")

    word = page.get_textpage(clip_rect)
    bbox = word.extractWORDS() # returns a list [x0, y0, x1, y1, "text", block_no, line_no, word_no]

    # WORKING WITH WORD EXTRACTION
    filtered_bbox_number = [entry for entry in bbox if not is_number_like(entry[4])]
    filtered_bbox_string_1 = [entry for entry in filtered_bbox_number if is_valid_room_name(entry[4])]
    filtered_bbox_string = [entry for entry in filtered_bbox_string_1 if has_more_than_one_char(entry[4])]
    combined_bbox = combine_close_words(filtered_bbox_string)

    for entry in combined_bbox:
        x0, y0, x1, y1 = entry[0], entry[1], entry[2], entry[3]
        rect= fitz.Rect(x0, y0, x1, y1)
        page.add_rect_annot(rect)
        
    doc.save(output_PDF)

    with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(combined_bbox,f, indent=2, ensure_ascii=False)
                print(f"Successfully saved extracted JSON to '{output_filename}'")

    # calculate the centerpoints of the room 
    centerpoints = []
    for entry in combined_bbox:
        centerpoint = calculate_bbox_center(entry)
        centerpoints.append(centerpoint)
    
    with open(output_centerpoints, 'w', encoding='utf-8') as f:
                json.dump(centerpoints,f, indent=2, ensure_ascii=False)
                print(f"Successfully saved extracted JSON to '{output_filename}'")
    # create voronoi polygons around the center points 
    page_width, page_height = page.rect.width, page.rect.height
    flipped_centerpoints = flip_y_coordinates(centerpoints,page_height)
    voronoi_polygons =process_simple_voronoi(flipped_centerpoints, flipped_rect)


