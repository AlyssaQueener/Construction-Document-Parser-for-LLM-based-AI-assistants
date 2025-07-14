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

def create_door_detection_prompt():
    """
    Create a prompt that instructs the model to extract the bounding boxes for doors.
    
    The required JSON structure is:
    {
      "doors": [
        {
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
    """
    prompt = """
You are an expert in reading architectural floor plans. Your task is to identify all the **doors** in the provided image and return the bounding boxes for each door.
Use the following structure for your output.

The image you're analyzing is exactly 2200 pixels wide and 1700 pixels high. Use these dimensions to compute and normalize all bounding boxes.

Return only a valid JSON object in this format:

{
    "doors": [
        {
            "bbox": {
             "x_min": value,  // left side (decimal percentage of image width, between 0.0 and 1.0)
        "y_min": value,  // bottom side (decimal percentage of image height, between 0.0 and 1.0)
        "x_max": value,  // right side (decimal percentage of image width, between 0.0 and 1.0)
        "y_max": value   // top side (decimal percentage of image height, between 0.0 and 1.0)
            }
        }
        // more doors if present
    ]
}
"""
    return prompt

def call_mistral_for_door_detection(image_path):
    """Call the Mistral API with an image to detect door bounding boxes."""
    base64_image = encode_image(image_path)
    if not base64_image:
        return {"error": "Unable to encode image"}
    
    prompt = create_door_detection_prompt()
    
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
        response_content = chat_response.choices[0].message.content
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON response: {str(e)}"}
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}


def save_door_results(results, output_file="door_detection_results_b1.json"):
    """Save the door detection results to a JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Door results saved to {output_file}")
    except Exception as e:
        print(f"Error saving door results: {str(e)}")

if __name__ == "__main__":
    image_path = "test4.png"  # Update with your actual image path

    # Run Door Detection
    door_result = call_mistral_for_door_detection(image_path)
    print("Door Detection Result:")
    print(json.dumps(door_result, indent=2))
    save_door_results(door_result)
