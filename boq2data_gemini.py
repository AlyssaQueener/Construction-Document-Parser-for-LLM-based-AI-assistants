import src.boq2data.camelot_setup.Camelot_Functions as cam 
import json
import camelot
import src.boq2data.camelot_setup.gemini as gemini 
import csv
import asyncio 

if __name__ == "__main__":
    path = 'examples/FinancialDocuments/Bill-of-Quantities-Sample2.pdf'
    flav = 'network'
    page_num = '1'
    #tables_boq4 = cam.cam_extract(path,flav,page_num)
   
   # unprocessed and processed values 
    tables = camelot.read_pdf(path, flavor=flav, pages=page_num)
    tables_boq_processed = cam.cam_stream_merge(tables)
    
    # Display tables in json and csv 
    print(tables)
#     tables.export('foo.csv',f='csv')

    print(tables_boq_processed)
#     fieldnames = sorted(tables_boq_processed[0].keys()) if tables_boq_processed else []
#     with open('output.csv', 'w', encoding='utf-8', newline='') as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(tables_boq_processed)

# Prepare processed input for gemini 
# stringify the json again 
    processed_str = json.dumps(tables_boq_processed, indent=2, ensure_ascii=False)
    #Step 1: Generate the prompt using your function
    prompt = gemini.create_preproccesed_prompt(tables_boq_processed)
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

    
