import src.plan2data.helper as helper


path = "examples/FloorplansAndSectionViews/Simple Floorplan/03_Simple.pdf"

images = helper.pdf_to_split_images(path, 0)

print(helper.extract_room_names_from_chunks(images))

