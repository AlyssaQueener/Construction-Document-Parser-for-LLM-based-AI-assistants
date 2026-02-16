import Attempts.Attempts_Rebekka.test_workflow_room_extraction as parser
import sys

if __name__ == "__main__":
    filename = "your png here"
    
    try:
        results = parser.process_floorplan(filename, lang='deu', show_visualization=True)
        print("\nProcessing complete!")
        print(f"Extracted text: {[item['text'] for item in results['text_data']]}")
    except Exception as e:
        print(f"Error processing floor plan: {e}")
        sys.exit(1)