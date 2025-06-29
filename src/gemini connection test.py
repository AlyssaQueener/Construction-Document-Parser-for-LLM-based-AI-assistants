import os
import google.generativeai as genai

def make_gemini_easy_call(prompt_text="Hello, Gemini! How are you today?"):
    """
    Makes a simple call to the Google Gemini API using the GOOGLE_API_KEY
    environment variable.
    """
    try:
        # 1. Retrieve and configure API key from environment variable
        api_key = os.environ["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        print("API Key configured from environment variable.")

        # 2. Initialize the Gemini-Pro model
        model = genai.GenerativeModel('gemini-2.5-flash')
        print(f"Sending prompt to Gemini: '{prompt_text}'")

        # 3. Make the generative call
        response = model.generate_content(prompt_text)

        # 4. Print the generated text
        print("\n--- Gemini's Response ---")
        print(response.text)
        print("-----------------------")

    except KeyError:
        print("\nERROR: GOOGLE_API_KEY environment variable is not set.")
        print("Please set it before running this script.")
        print("For example (PowerShell): $env:GOOGLE_API_KEY=\"YOUR_API_KEY\"")
        print("Or (Linux/macOS): export GOOGLE_API_KEY=\"YOUR_API_KEY\"")
    except Exception as e:
        print(f"\nAN ERROR OCCURRED DURING GEMINI API CALL:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e}")
        print("\nTroubleshooting tips:")
        print("- Double-check your API key's validity on Google AI Studio.")
        print("- Ensure you have an active internet connection.")
        print("- Verify the 'gemini-pro' model is accessible with your key.")

if __name__ == "__main__":
    # You can change the prompt here if you like
    make_gemini_easy_call(prompt_text="What is the capital of France?")
    # make_gemini_easy_call(prompt_text="Tell me a very short, cheerful story about a robot.")