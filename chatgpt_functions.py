# chatgpt_functions.py

from dotenv import load_dotenv
import os
from openai import OpenAI
from search_function import search_arxiv_articles
from document_functions import create_word_doc_from_json
from datetime import datetime

# Load environment variables from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Check if API key is set
if client.api_key is None:
    raise Exception("OpenAI API key not found. Make sure it is set in the .env file.")

# Function to get ChatGPT response using RAG architecture
def get_chatgpt_response(research_topic, citation_format):
    # Search on ArXiv
    search_results = search_arxiv_articles(research_topic)

    # Structure input for ChatGPT (RAG approach)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Summarize the abstracts of the following ArXiv articles about {research_topic}:"},
        {"role": "user", "content": "\n".join([f"Title: {res['title']}, Abstract: {res['summary']}" for res in search_results])}
    ]
    
    try:
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        response_text = completion.choices[0].message.content.strip()

        # Create folder

        folder_name = "generated_outputs"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)


        # -> Every file is created per response
        # -> Every response is saved into folder
        
        # Unique filename ({research_topic}_Response_{citation_format})

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename=f'{folder_name}/{research_topic}_Response_{citation_format}_{timestamp}.docx'

        # Save response in a Word document with citation format
        create_word_doc_from_json({
            'research_topic': research_topic,
            'response': response_text,
            'citation_format': citation_format,
            'articles': search_results
        }, filename = filename)
        
        return response_text
    
    except Exception as e:
        return f"An error occurred: {e}"
