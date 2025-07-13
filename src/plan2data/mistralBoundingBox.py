from mistralai import Mistral
import base64
import os
import json

# --- Configuration ---
api_key = "mVTgI1ELSkn5Q28v2smHK0O4E02nMaxG"
model = "mistral-small-latest"  
client = Mistral(api_key=api_key)

def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_room_detection_prompt():
    """
    Create a prompt that instructs the model to extract the bounding boxes for rooms.
    
    The required JSON structure is:
    
    {
      "rooms": [
        {
          "name": "Room Name or null",
          "bbox": {
            "x_min": <decimal between 0.0 and 1.0>,
            "y_min": <decimal between 0.0 and 1.0>,
            "x_max": <decimal between 0.0 and 1.0>,
            "y_max": <decimal between 0.0 and 1.0>
          }
        },
        ...
      ]
    }
    
    If room names are not visible, return "name": null.
    """
    prompt = """
You are an expert in understanding architectural floor plans. Your task is to identify all the rooms in the provided image and return the bounding boxes for each room.
For each room you find, return a JSON object with the following structure:

{
  "rooms": [
    {
      "name": "Room Name or null",
      "bbox": {
        "x_min": value,  // left side (decimal percentage of image width, between 0.0 and 1.0)
        "y_min": value,  // bottom side (decimal percentage of image height, between 0.0 and 1.0)
        "x_max": value,  // right side (decimal percentage of image width, between 0.0 and 1.0)
        "y_max": value   // top side (decimal percentage of image height, between 0.0 and 1.0)
      }
    }
    // ... more rooms if present
  ]
}

Please return only a valid JSON object exactly following the above structure.
"""
    return prompt

def call_mistral_for_room_detection(image_path):
    """Call the Mistral API with an image to detect room bounding boxes."""
    base64_image = encode_image(image_path)
    if not base64_image:
        return {"error": "Unable to encode image"}
    
    prompt = create_room_detection_prompt()
    
    # Create the message as a list with text and image parts.
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }}
            ]
        }
    ]
    
    try:
        chat_response = client.chat.complete(
            model=model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        # Parse the JSON response content and return as a Python dict
        response_content = chat_response.choices[0].message.content
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON response: {str(e)}"}
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}

def save_results_to_file(results, output_file="room_detection_results2.json"):
    """Save the results to a JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Error saving results: {str(e)}")

# --- Example Usage ---
if __name__ == "__main__":
    # Replace 'floorplan.jpg' with the path to your floor plan image.
    result = call_mistral_for_room_detection("bemasster-grundriss-plankopf_page1.png")
    
    # Print the JSON result
    print(json.dumps(result, indent=2))
    
    # Optionally save to file
    save_results_to_file(result)