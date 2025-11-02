import base64
import json
import requests
import os
from mistralai import Mistral


model = "mistral-small-latest"
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
image_path = "test5.png"  # Your local image path
# === STRUCTURED PROMPT ===
question = (
    "You are an assistant that extracts structured data from architectural floor plans. "
    "Given the image, return all title block metadata and a list of rooms and their spatial relationships. "
    "Use exactly this JSON format:\n\n"
    "{\n"
    "  \"titleBlock\": {\n"
    "    \"projectName\": \"string\",\n"
    "    \"architect\": \"string\",\n"
    "    \"client\": \"string\",\n"
    "    \"location\": \"string\",\n"
    "    \"author\": \"string\",\n"
    "    \"engineers\": [\"string\"],\n"
    "    \"yearOfCompletion\": \"string\",  \n"
    "    \"approvalDate\": \"string\",\n"
    "    \"date\": \"string\",\n"
    "    \"planType\": \"string\",\n"
    "    \"scale\": \"string\"\n"
    "  },\n"
    "  \"rooms\": [\n"
    "    {\n"
    "      \"roomName\": \"string\",\n"
    "      \"area\": null,  # or number, if labeled\n"
    "      \"adjacentRooms\": [\"string\"],\n"
    "      \"neighboringRooms\": [\"string\"]\n"
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Instructions:\n"
    "- Fill all title block fields with values found on the drawing. If a field is missing, use null or an empty string.\n"
    "- For boundingBox, use normalized coordinates (0–1).\n"
    "- For rooms, list every detected room with its name and bounding box, area if labeled, and adjacency/neighbors using room names from the plan.\n"
    "- Return ONLY proper JSON—do not output explanations, headers, or code.\n"
)



# === ENCODE IMAGE AS BASE64 ===
with open(image_path, "rb") as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

# === PREPARE API REQUEST ===
url = "https://api.mistral.ai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "mistral-large-latest",  # ✅ Must be this or "mistral-small-latest"
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }
    ]
}

# === SEND REQUEST ===
response = requests.post(url, headers=headers, json=data)

# === HANDLE RESPONSE ===
if response.status_code == 200:
    result = response.json()
    print("\n=== MISTRAL RESPONSE ===\n")
    print(result['choices'][0]['message']['content'])
else:
    print(f"\nError {response.status_code}:\n{response.text}")


# === HANDLE RESPONSE ===
if response.status_code == 200:
    result = response.json()
    content = result["choices"][0]["message"]["content"]

    print("\n=== MISTRAL RESPONSE ===\n")
    print(content)

    # === SAVE OUTPUT TO JSON FILE ===
    try:
        parsed_json = json.loads(content)  # ensure it's valid JSON
        output_file = "output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Output saved to '{output_file}'")
    except json.JSONDecodeError:
        print("\n⚠️ Warning: The model response is not valid JSON and was not saved.")
else:
    print(f"\nError {response.status_code}:\n{response.text}")


