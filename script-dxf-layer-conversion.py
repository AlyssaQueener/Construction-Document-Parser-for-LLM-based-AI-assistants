import Attempts.Attempts_Rebekka.convert_pdf_to_dxf as dxf

if __name__ == '__main__':
    # Configuration
    pdf_path = "examples/FloorplansAndSectionViews/Simple Floorplan/01_Simple.pdf"
    # pdf_path = "examples/FloorplansAndSectionViews/BasicTestPlan.pdf"
    
    output_path = "converted_output_with_text_and_curves.dxf"
    
    # Run conversion
    result = dxf.convert_pdf_to_dxf(pdf_path, output_path)
    
    if result['success']:
        print(f"\n✅ Conversion completed successfully!")
        print(f"   Output: {result['output_file']}")
        print(f"   Total entities: {result['total_entities']}")
        print(f"   Pages processed: {result['pages_processed']}")
    else:
        print(f"\n❌ Conversion failed: {result.get('error', 'Unknown error')}")