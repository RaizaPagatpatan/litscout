# chatgpt_functions.py

import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from search_function import search_arxiv_articles

# Load environment variables
load_dotenv()

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_chatgpt_response(research_topic, related_topic, field_of_study, type_of_publication, date_range, keywords, citation_format):
    """Generates a response by retrieving and processing articles."""
   
    # Construct query
    query = research_topic
    if related_topic:
        query += f" related to {related_topic}"
    if field_of_study != "-- Select --":
        query += f" in {field_of_study}"
    if type_of_publication != "-- Select --":
        query += f" {type_of_publication}"
    if keywords:
        query += f" keywords: {keywords}"

    # Search for articles
    search_results = search_arxiv_articles(query, date_range)

    # Use OpenAI to generate response
    try:
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a research assistant that provides comprehensive and academic summaries."},
                {"role": "user", "content": f"Provide a comprehensive research summary on: {query}. Use these articles for context: {', '.join([article['title'] for article in search_results])}"}
            ]
        )
        final_response = chat_response.choices[0].message.content
    except Exception as e:
        final_response = f"Error generating response: {str(e)}"

    # Create/ retrieve collections
    try:
        collection = chroma_client.get_or_create_collection(name="arxiv_embeddings")
        
        # Store article summaries in ChromaDB
        for idx, article in enumerate(search_results):
            collection.add(
                documents=[article['summary']],
                metadatas=[{"title": article['title'], "url": article['url']}],
                ids=[f"article_{idx}"]
            )
    except Exception as e:
        print(f"ChromaDB storage error: {e}")

    return {
        'research_topic': research_topic,
        'response': final_response,
        'articles': search_results,
        'citation_format': citation_format,
        'field_of_study': field_of_study,
        'type_of_publication': type_of_publication
    }
