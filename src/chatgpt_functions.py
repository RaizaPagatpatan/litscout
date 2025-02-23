# chatgpt_functions.py

import os
from dotenv import load_dotenv
from openai import OpenAI
# from pinecone import Pinecone, ServerlessSpec
import pinecone
import logging
#langchain imports
from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_pinecone import Pinecone as LangchainPinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from search_function import search_arxiv_articles, search_articles

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required environment variables
# pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_api_key = pinecone.Pinecone(api_key= os.getenv("PINECONE_API_KEY"))
openai_api_key = os.getenv("OPENAI_API_KEY")

if not pinecone_api_key:
    raise ValueError(
        "PINECONE_API_KEY environment variable is not set. "
        "Please set it in your Streamlit deployment settings."
    )

if not openai_api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it in your Streamlit deployment settings."
    )

# Initialize Pinecone with explicit API key
pc = Pinecone(
    api_key=pinecone_api_key  # Use the explicitly loaded API key
)

# Initialize OpenAI clients with explicit API keys
client = OpenAI(api_key=openai_api_key)
embeddings = OpenAIEmbeddings(
    api_key=openai_api_key,
    model="text-embedding-3-small"
)

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
    
    logger.info(f"Prepared {len(docs)} documents for embedding")
    return docs

def create_vector_store(articles):
    """
    Create a vector store from articles using Pinecone and OpenAI embeddings
    """
    # Log the input articles for debugging
    logger.info(f"Creating vector store. Input articles type: {type(articles)}")
    logger.info(f"Number of input articles: {len(articles) if hasattr(articles, '__len__') else 'Unknown'}")
    
    # Validate input
    if not articles:
        logger.warning("No articles provided for vector store creation")
        return None
    
    try:
        # Ensure articles is a list
        if not isinstance(articles, list):
            articles = list(articles)
        
        # Prepare documents
        docs = prepare_documents_for_embedding(articles)
        
        if not docs:
            logger.warning("No documents were prepared for embedding")
            return None

        # Create or get existing index
        index_name = "litscout-articles"
        
        try:
            # Check if index exists
            existing_indexes = pc.list_indexes().names()
            
            # Create index if it doesn't exist
            if index_name not in existing_indexes:
                logger.info(f"Creating new index: {index_name}")
                pc.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI embeddings dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                # Wait for index to be ready
                import time
                time.sleep(10)  # Give some time for index to initialize
            
            logger.info(f"Using index: {index_name}")
            
            # Initialize Pinecone vector store with LangChain
            vector_store = LangchainPinecone.from_documents(
                docs,
                embeddings,
                index_name=index_name
            )
            
            logger.info(f"Successfully created vector store with {len(docs)} documents")
            return vector_store
            
        except Exception as e:
            logger.error(f"Pinecone index error: {str(e)}")
            raise
    
    except Exception as e:
        logger.error(f"Vector store creation error: {str(e)}")
        # Log the first few articles for debugging
        if articles:
            logger.error(f"First article details: {articles[0]}")
        return None

def retrieve_relevant_context(vector_store, query, top_k=3):
    """
    Retrieve most relevant context from vector store
    """
    # Check if vector store is None or invalid
    if vector_store is None:
        logger.warning("No vector store provided for context retrieval")
        return ""
    
    try:
        # Retrieve relevant documents
        relevant_docs = vector_store.similarity_search(query, k=top_k)
        
        # If no relevant documents found
        if not relevant_docs:
            logger.info("No relevant context found")
            return ""
        
        # Extract and format context
        context = "\n\n".join([
            f"Document {i+1}: {doc.page_content}" 
            for i, doc in enumerate(relevant_docs)
        ])
        
        logger.info(f"Retrieved {len(relevant_docs)} relevant context documents")
        return context
    
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        return ""

def get_chatgpt_response(
    research_topic, 
    related_topic, 
    field_of_study, 
    type_of_publication, 
    date_range, 
    keywords, 
    citation_format, 
    open_access_site):
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

    if vector_store is None:
        logger.warning("No vector store provided for context retrieval")
        return ""
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