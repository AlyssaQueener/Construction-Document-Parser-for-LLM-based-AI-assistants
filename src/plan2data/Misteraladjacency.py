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

def create_room_adjacency_prompt():
    """
    Create a prompt that instructs the model to extract room adjacencies (which rooms are connected).
    
    The required JSON structure is:
    {
      "adjacencies": {
        "Room Name A": ["Room Name B", "Room Name C"],
        "Room Name B": ["Room Name A"],
        ...
      }
    }
    """
    prompt = """
You are an expert in reading architectural floor plans. Your task is to analyze the floor plan image and determine **which rooms are directly connected to each other**.

Two rooms are considered connected if they share a **door**, **open passage**, or **direct access** through any visible architectural opening. Shared walls alone do not imply connectivity unless there is a door or opening.

**Step 1**: Identify the room names or mark them as "Room_1", "Room_2", etc., if no name is available.

**Step 2**: For each room, list the other rooms it is directly connected to, based on visible openings in the floor plan.

The image is 2200 pixels wide and 1700 pixels high. Use this scale for any positional reasoning you do internally, but your final output should only be this JSON:

{
  "adjacencies": {
    "Bedroom": ["Kitchen", "Hallway"],
    "Kitchen": ["Bedroom", "Dining Room"],
    "Room_1": ["Room_2"],
    ...
  }
}

Please return only a **valid JSON** with the exact format shown above.
"""
    return prompt


def call_mistral_for_room_adjacency(image_path):
    """Call the Mistral API with an image to detect room adjacencies."""
    base64_image = encode_image(image_path)
    if not base64_image:
        return {"error": "Unable to encode image"}

    prompt = create_room_adjacency_prompt()

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


def save_room_results(results, output_file="room_adjacency_results_a1.json"):
    """Save the room adjacency results to a JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Room results saved to {output_file}")
    except Exception as e:
        print(f"Error saving room results: {str(e)}")

if __name__ == "__main__":
    image_path = "bemasster-grundriss-plankopf_page1.png"  # Update with your actual image path

    # Run Room Adjacency Detection
    room_result = call_mistral_for_room_adjacency(image_path)
    print("Room Adjacency Detection Result:")
    print(json.dumps(room_result, indent=2))
    save_room_results(room_result)
