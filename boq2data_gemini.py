import src.boq2data.camelot_setup.Camelot_Functions as cam 
import json
import camelot
import src.boq2data.camelot_setup.gemini as gemini 
import os


def financial_boq(path):
    """
    Complete pipeline for extracting structured data from BOQ PDF documents.
    
    This function orchestrates the entire BOQ extraction process:
    1. Extracts tables from PDF using Camelot
    2. Merges broken lines and preprocesses data
    3. Sends to Gemini API for intelligent field extraction
    4. Returns structured JSON output
    
    Args:
        path (str): File path to the BOQ PDF document
    
    Returns:
        dict: Structured JSON containing sections, items, and financial data
              organized according to BOQ schema (see create_preprocessed_prompt)
    
    Pipeline:
        PDF → Camelot extraction → Line merging → JSON preprocessing 
        → Gemini prompt → API call → Structured JSON
    
    Note:
        - Uses 'stream' flavor for best BOQ extraction results
        - Processes all pages in the document
        - Relies on Gemini AI for flexible field matching
    """
    # Configuration
    page_num = "all"  # Process all pages in the PDF
    flav = "stream"   # Use stream flavor (best performance for BOQs)
    
    # Step 1: Extract tables from PDF using Camelot
    tables = camelot.read_pdf(path, flavor=flav, pages=page_num)  # Output: Camelot table object
    
    # Step 2: Merge broken lines and flatten table structure to JSON
    tables_boq_processed = cam.cam_stream_merge(tables)  # Output: List of dicts (JSON-like)
    
    # Step 3: Convert processed data to JSON string for prompt
    processed_str = json.dumps(tables_boq_processed, indent=2, ensure_ascii=False)
    
    # Step 4: Create prompt with extraction instructions and preprocessed data
    prompt = gemini.create_preprocessed_prompt(processed_str)
    
    # Step 5: Send to Gemini API and receive structured JSON response
    response_json = gemini.call_gemini_return_json(prompt)
    
    return response_json
       



if __name__ == "__main__":
    path = 'examples/FinancialDocuments/BOQ2.pdf'
    flav = 'stream'
    page_num = 'all'
    #tables_boq4 = cam.cam_extract(path,flav,page_num)
   
   # unprocessed and processed values 
    tables = camelot.read_pdf(path, flavor=flav, pages=page_num) # type: ignore # -> output camelot table object 
    #camelot.plot(tables[0], kind='text').show()
    
    tables_boq_processed = cam.cam_stream_merge(tables) # json 
    
###### # Display tables in json and csv 
    print(tables)
#     tables.export('foo.csv',f='csv')

    print(tables_boq_processed)
    # fieldnames = sorted(tables_boq_processed[0].keys()) if tables_boq_processed else []
    # with open('output.csv', 'w', encoding='utf-8', newline='') as f:
    #     writer = csv.DictWriter(f, fieldnames=fieldnames)
    #     writer.writeheader()
    #     writer.writerows(tables_boq_processed)

#Prepare processed input for gemini 
#stringify the json again 
    processed_str = json.dumps(tables_boq_processed, indent=2, ensure_ascii=False)
    #Step 1: Generate the prompt using your function
    prompt = gemini.create_preprocessed_prompt(processed_str)
    print("---- PROMPT SENT TO GEMINI ----")
    print(prompt)
    print("---- END OF PROMPT ----")

   # Step 2: Call Gemini and get the parsed JSON
    response_json = gemini.call_gemini_return_json(prompt)

    output_folder = "output/Financial"
    output_file = "BOQ2_extracted_boq_data.json"
    output_path = os.path.join(output_folder, output_file)
    os.makedirs(output_folder, exist_ok=True)
    print(response_json)
    with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(response_json, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved extracted JSON to '{output_path}'")

    
