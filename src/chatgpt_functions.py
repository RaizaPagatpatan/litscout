# chatgpt_functions.py

import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
import logging
#langchain imports
from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from search_function import search_arxiv_articles, search_articles

# from search_function import search_arxiv_articles

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create logger for this module
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Initialize OpenAI clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

def prepare_documents_for_embedding(articles):
    """
    Prepare articles for embedding by splitting long texts
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len
    )
    
    docs = []
    for article in articles:
        try:
            # Get the text content (either summary or abstract)
            text_content = article.get('summary', article.get('abstract', ''))
            
            # Convert authors list to string if necessary
            authors = article.get('authors', [])
            if isinstance(authors, list):
                authors = ', '.join(authors)
            
            # Title and content
            full_text = f"Title: {article['title']} Content: {text_content}"
            splits = text_splitter.split_text(full_text)
            
            # Get metadata with fallbacks for optional fields
            metadata = {
                'title': article['title'],
                'url': article.get('url', ''),
                'authors': authors,
                'source': article.get('metadata', {}).get('source', '')
            }
            
            # Add optional PMID if available
            if 'pmid' in article.get('metadata', {}):
                metadata['pmid'] = article['metadata']['pmid']
            
            for split in splits:
                docs.append(Document(
                    page_content=split,
                    metadata=metadata
                ))
        except Exception as e:
            logger.error(f"Error processing article for embedding: {e}")
            continue
    
    return docs

def create_vector_store(articles):
    """
    Create a vector store from articles using ChromaDB and OpenAI embeddings
    """
    try:
        if not articles:
            logger.warning("No articles provided for vector store creation")
            return None
            
        # Pre-process documents for embedding
        docs = prepare_documents_for_embedding(articles)
        
        if not docs:
            logger.warning("No documents created after preprocessing")
            return None
        # Pre-process documents for embedding
        docs = prepare_documents_for_embedding(articles)
        
        # Create Chroma vector store
        vector_store = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory="./chroma_db",
            collection_metadata={"hnsw:space": "cosine"}
        )
        
        return vector_store
    except Exception as e:
        logger.error(f"Error creating vector store: {e}")
        print(f"Error creating vector store: {e}")
        return None

def retrieve_relevant_context(vector_store, query, top_k=3):
    """
    Retrieve most relevant context from vector store
    """
    if vector_store is None:
        return ""
    
    try:
        # Retrieve top k most similar document chunks (data with relative topics or context.. etc)
        relevant_docs = vector_store.similarity_search(query, k=top_k)
        
        # Format retrieved context
        context = "\n\n".join([
            f"Relevant Document {i+1}:\n{doc.page_content}\n(From: {doc.metadata['title']})" 
            for i, doc in enumerate(relevant_docs)
        ])
        
        return context
    except Exception as e:
        print(f"Error retrieving context: {e}")
        return ""

def get_chatgpt_response(research_topic, related_topic, field_of_study, type_of_publication, date_range, keywords, citation_format, open_access_site):
    """
    Enhanced response generation with RAG
    """
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

    # Search for articles via 1 openSourceDB for articles for the mean time. Add more when data source input field is specified in app.py
    # search_results = search_arxiv_articles(query, date_range)
    search_results = search_articles(query, date_range, open_access_site)

    # word -> vec (Create vector store)
    vector_store = create_vector_store(search_results)

    # Retrieve relevant context
    context = retrieve_relevant_context(vector_store, query)

    # Use OpenAI to generate response with retrieved context (Semantic decomposition by providing the AI assistant about the intent of the qquery)
    try:
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a research assistant that provides comprehensive and academic summaries. Use the provided context retrieved from the embeddings to enhance your response."
                },
                {
                    "role": "user", 
                    "content": f"Provide a comprehensive research summary on: {query}. "
                               f"Use these contextually relevant document excerpts: {context}"
                }
            ]
        )
        final_response = chat_response.choices[0].message.content
    except Exception as e:
        final_response = f"Error generating response: {str(e)}"

    return {
        'research_topic': research_topic,
        'response': final_response,
        'articles': search_results,
        'citation_format': citation_format,
        'field_of_study': field_of_study,
        'type_of_publication': type_of_publication
        
    }