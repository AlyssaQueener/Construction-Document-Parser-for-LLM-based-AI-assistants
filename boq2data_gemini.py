import src.boq2data.camelot_setup.Camelot_Functions as cam 
import json
import src.boq2data.camelot_setup.gemini as gemini 
import asyncio 

if __name__ == "__main__":
    path = 'examples/FinancialDocuments/BoQExample.pdf'
    flav = 'hybrid'
    page_num = '1'
    tables_boq4 = cam.cam_extract(path,flav,page_num)
    #tables = cam_extract_accuracy(path,page_num)
    
    tables_boq_processed = cam.cam_stream_merge(tables_boq4)
    # stringify the json again 
    processed_str = json.dumps(tables_boq_processed, indent=2, ensure_ascii=False)
    
    # Step 1: Generate the prompt using your function
    prompt = gemini.create_extraction_prompt(processed_str)
    print("---- PROMPT SENT TO GEMINI ----")
    print(prompt)
    print("---- END OF PROMPT ----")
    # Step 2: Call Gemini and get the parsed JSON
    response_json = gemini.call_gemini_return_json(prompt)
    output_filename = "extracted_boq_data.json"
    print(response_json)
    with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(response_json, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved extracted JSON to '{output_filename}'")

    
