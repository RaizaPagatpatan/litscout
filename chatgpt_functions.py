# chatgpt_functions.py
from dotenv import load_dotenv
import os
from openai import OpenAI
from document_functions import create_word_doc_from_json  # Import the document function

# Load environment variables from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Check if API key is set
if client.api_key is None:
    raise Exception("OpenAI API key not found. Make sure it is set in the .env file.")

# Function to get ChatGPT response
def get_chatgpt_response(user_message):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message}
    ]
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        # Parse the response
        response_json = completion.to_dict()
        
        # Save the JSON response to a Word document
        create_word_doc_from_json(response_json, filename='chatgpt_response.docx')
        
        return completion.choices[0].message.content.strip()
    
    except Exception as e:
        return f"An error occurred: {e}"
