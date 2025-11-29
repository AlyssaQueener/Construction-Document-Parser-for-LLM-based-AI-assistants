import src.boq2data.camelot_setup.Camelot_Functions as cam 
import json
import camelot
import src.boq2data.camelot_setup.gemini as gemini 



from mistralai import Mistral
import base64
import os

## Retrieve the API key from environment variables
#api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-small-2503"
api_key_r = "bXBteq8WKzIBDINDeBy4ZmHc9QdAMZMQ"
client = Mistral(api_key=api_key_r)

def call_mistral_boq(path):
        page_num = "all"
        flav = "stream"
        tables = camelot.read_pdf(path, flavor=flav, pages=page_num) # -> output camelot table object 
        tables_boq_processed = cam.cam_stream_merge(tables) # json 
        processed_str = json.dumps(tables_boq_processed, indent=2, ensure_ascii=False)
        user_message = gemini.create_preproccesed_prompt(processed_str)
        messages = [
        {
            "role": "system",
            "content": "You are a JSON extraction assistant. You MUST return a JSON object with exactly two keys: 'Sections' (array) and 'confidence' (number). Never return a bare array."
        },
        {
            "role": "user",
            "content": user_message,
        }
    ]
        chat_response = client.chat.complete(
        model = model,
        messages = messages,
        response_format = {
            "type": "json_object",
        }
        )
        response = chat_response.choices[0].message.content
        # Clean the response
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        # DEBUG: Print what we're getting back
        # print("=" * 80)
        # print("RAW LLM RESPONSE:")
        # print(response[:1000])  # First 1000 chars
        # print("=" * 80)

        return response

def extract_boq_mistral(path):
    is_success = False
    method = "hybrid"
    response = call_mistral_boq(path)
    #cleaned_response = response.strip().removeprefix('```json\n').removesuffix('\n```')

    try:
        # Attempt to parse the response as JSON
        import json
        output = json.loads(response)
        
        # Handle if output is a list instead of dict
        if isinstance(output, list):
            print("Warning: LLM returned a list instead of expected object structure")
            # Wrap the list in the expected structure
            output = {
                "Sections": output,
                "confidence": 0.5  # Default confidence since structure wasn't followed
            }
        
        # Now safely get confidence
        confidence = output.get("confidence", 0)
        
        if confidence > 0.5:
            is_success = True
        
        return output, method, is_success
        
    except json.JSONDecodeError as e:
        return {"error": "Response is not valid JSON", "raw_response": response}, method, False, 0
    

       
def financial_boq(path):
        page_num = "all"
        flav = "stream"
        is_success=False
        method = "hybrid"
        tables = camelot.read_pdf(path, flavor=flav, pages=page_num) # -> output camelot table object 
        tables_boq_processed = cam.cam_stream_merge(tables) # json 
        processed_str = json.dumps(tables_boq_processed, indent=2, ensure_ascii=False)
        #prompt = gemini.create_preproccesed_prompt(processed_str)
        response_json = {
              "Under":"Construction"
        }
        #response_json = gemini.call_gemini_return_json(prompt)
        if response_json:
              is_success = True
        return response_json, method, is_success
       



if __name__ == "__main__":
    path = "Construction-Document-Parser-for-LLM-based-AI-assistants/examples/FinancialDocuments/BOQ.pdf"
    extract_boq_mistral(path)

#     path = 'examples/FinancialDocuments/Bill-of-Quantities-Sample2.pdf'
#     flav = 'stream'
#     page_num = 'all'
#     #tables_boq4 = cam.cam_extract(path,flav,page_num)
   
#    # unprocessed and processed values 
#     tables = camelot.read_pdf(path, flavor=flav, pages=page_num) # type: ignore # -> output camelot table object 
#     #camelot.plot(tables[0], kind='text').show()
    
#     tables_boq_processed = cam.cam_stream_merge(tables) # json 
    
# ###### # Display tables in json and csv 
#     print(tables)
# #     tables.export('foo.csv',f='csv')

#     print(tables_boq_processed)
#     fieldnames = sorted(tables_boq_processed[0].keys()) if tables_boq_processed else []
#     with open('output.csv', 'w', encoding='utf-8', newline='') as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(tables_boq_processed)

# #Prepare processed input for gemini 
# #stringify the json again 
#     processed_str = json.dumps(tables_boq_processed, indent=2, ensure_ascii=False)
#     #Step 1: Generate the prompt using your function
#     prompt = gemini.create_preproccesed_prompt(processed_str)
#     print("---- PROMPT SENT TO GEMINI ----")
#     print(prompt)
#     print("---- END OF PROMPT ----")

#    # Step 2: Call Gemini and get the parsed JSON
#     response_json = gemini.call_gemini_return_json(prompt)
#     output_filename = "extracted_boq_data.json"
#     print(response_json)
#     with open(output_filename, 'w', encoding='utf-8') as f:
#             json.dump(response_json, f, indent=2, ensure_ascii=False)
#     print(f"Successfully saved extracted JSON to '{output_filename}'")