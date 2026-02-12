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

def create_room_detection_prompt(image_width=2200, image_height=1700):
    """
    Generate a prompt for Mistral to detect rooms and return normalized bounding boxes.
    """
    return f"""
You are an expert in understanding architectural floor plans.

The image you're analyzing is exactly {image_width} pixels wide and {image_height} pixels high. 
Use these dimensions to compute and normalize all bounding boxes. 
All values should be returned as decimal percentages between 0.0 and 1.0.

Your task is to identify all the rooms in the image and return the bounding boxes for each room 
as a JSON object in the following format (no explanations, only valid JSON):

{{
  "rooms": [
    {{
      "name": "Room Name or null",
      "bbox": {{
        "x_min": <decimal between 0.0 and 1.0>,  // left edge (x coordinate of bounding box start / image width)
        "y_min": <decimal between 0.0 and 1.0>,  // bottom edge (y coordinate of bounding box start / image height)
        "x_max": <decimal between 0.0 and 1.0>,  // right edge (x coordinate of bounding box end / image width)
        "y_max": <decimal between 0.0 and 1.0>   // top edge (y coordinate of bounding box end / image height)
      }}
    }}
    // ... more rooms if present
  ]
}}

If the room name is not visible, return "name": null. 
Only return the JSON, without additional explanation or formatting.
"""

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

def save_results_to_file(results, output_file="room_detection_results_a1.json"):
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
    result = call_mistral_for_room_detection("test4.png")
    
    # Print the JSON result
    print(json.dumps(result, indent=2))
    
    # Optionally save to file
    save_results_to_file(result)