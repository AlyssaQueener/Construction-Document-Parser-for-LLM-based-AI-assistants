import cairosvg
import os

def convert_pdf_to_svg(input_pdf_path, output_svg_path="output.svg"):
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"File not found: {input_pdf_path}")

    try:
        # Convert PDF to SVG
        cairosvg.svg_from_pdf(
            file_obj=open(input_pdf_path, "rb"),
            write_to=output_svg_path
        )
        print(f"SVG saved as: {output_svg_path}")
    except Exception as e:
        print("Error converting PDF to SVG:", e)

# Example usage
convert_pdf_to_svg("test4.pdf", "floorplan_converted.svg")
