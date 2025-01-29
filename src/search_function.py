# search_function.py

import requests
from datetime import datetime
import logging
import time
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def search_articles(query, date_range, open_access_site):
    """
    Search articles based on selected database
    """
    if open_access_site.lower() == "arxiv":
        print("Searching Arxiv...")
        return search_arxiv_articles(query, date_range)
    elif open_access_site.lower() == "pubmed":
        return search_pubmed_articles(query, date_range)
    else:
        logger.error(f"Unsupported database: {open_access_site}")
        return []

def search_arxiv_articles(query, date_range):
    """Searches for articles on ArXiv based on the query and date range."""
    
    start_year, end_year = date_range
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": 10,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        # Parse XML response
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        # Define namespaces
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        articles = []
        for entry in root.findall('atom:entry', ns):
            try:
                title = entry.find('atom:title', ns).text
                summary = entry.find('atom:summary', ns).text
                published = entry.find('atom:published', ns).text
                url = entry.find('atom:id', ns).text
                
                # Extract authors
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                
                # Check publication year
                published_year = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").year
                
                if start_year <= published_year <= end_year:
                    articles.append({
                        'title': title,
                        'summary': summary,
                        'authors': authors,
                        'published': published,
                        'url': url
                    })
            except Exception as e:
                logger.error(f"Error processing article: {e}")
        return articles
    except requests.RequestException as e:
        logger.error(f"Error retrieving data from ArXiv: {e}")
        return []

def search_pubmed_articles(query, date_range):
    """
    Searches for articles on PubMed based on the query and date range.
    Returns formatted articles suitable for vector store creation.
    """
    start_year, end_year = date_range
    pubmed_api_key = os.getenv("PUBMED_API_KEY")
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    if not pubmed_api_key:
        raise ValueError("PUBMED_API_KEY not found in environment variables")

    try:
        # Format query using PubMed's search field tags
        sanitized_query = query.replace('"', '').replace('[', '').replace(']', '')
        formatted_query = f'{sanitized_query} AND ("{start_year}/01/01"[Date - Publication] : "{end_year}/12/31"[Date - Publication])'

        logger.info(f"Formatted PubMed query: {formatted_query}")

        # Step 1: Get article IDs using esearch
        search_params = {
            "db": "pubmed",
            "term": formatted_query,
            "api_key": pubmed_api_key,
            "retmax": 20,  # Limit results for testing
            "retmode": "json"
        }

        search_url = f"{base_url}/esearch.fcgi"
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()

        search_data = search_response.json()
    
        # logger.debug(f"PubMed Search Response: {search_data}")

        id_list = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not id_list:
            logger.warning(f"No results found for query: {formatted_query}")
            return []

        # Step 2: Fetch article details using efetch
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "api_key": pubmed_api_key,
            "retmode": "xml"
        }

        fetch_url = f"{base_url}/efetch.fcgi"
        fetch_response = requests.get(fetch_url, params=fetch_params)
        fetch_response.raise_for_status()

        try:
            root = ET.fromstring(fetch_response.content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse PubMed XML response: {e}")
            return []

        articles = []

        for article in root.findall(".//PubmedArticle"):
            try:
                article_data = {}

                # Get title
                title_elem = article.find(".//ArticleTitle")
                article_data['title'] = title_elem.text if title_elem is not None else "No title available"

                # Get abstract
                abstract_texts = article.findall(".//Abstract/AbstractText")
                if abstract_texts:
                    abstract_parts = [
                        (abstract_elem.get('Label', '') + ": " if abstract_elem.get('Label') else '') + (abstract_elem.text or '')
                        for abstract_elem in abstract_texts
                    ]
                    article_data['abstract'] = ' '.join(abstract_parts)
                else:
                    article_data['abstract'] = "No abstract available"

                # Get authors
                authors = []
                author_list = article.findall(".//Author")
                for author in author_list:
                    lastname = author.find(".//LastName")
                    firstname = author.find(".//ForeName")
                    if lastname is not None:
                        author_name = lastname.text if firstname is None else f"{firstname.text} {lastname.text}"
                        authors.append(author_name)

                article_data['authors'] = authors if authors else ["Unknown Author"]

                # Get publication date
                pub_date = article.find(".//PubDate")
                if pub_date is not None:
                    year = pub_date.find(".//Year")
                    if year is not None:
                        article_data['published'] = year.text
                    else:
                        article_data['published'] = "N/A"

                # Get PMID and URL
                pmid_elem = article.find(".//PMID")
                if pmid_elem is not None:
                    article_data['pmid'] = pmid_elem.text
                    article_data['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_elem.text}/"

                # Format content for vector store
                article_data['content'] = f"Title: {article_data['title']}\nAuthors: {', '.join(article_data['authors'])}\nAbstract: {article_data['abstract']}\nURL: {article_data.get('url', 'No URL available')}"

                # Metadata for vector store
                article_data['metadata'] = {
                    'source': 'PubMed',
                    'title': article_data['title'],
                    'authors': ', '.join(article_data['authors']),
                    'url': article_data.get('url', ''),
                    'pmid': article_data.get('pmid', ''),
                    'published': article_data.get('published', 'N/A')
                }

                articles.append(article_data)

            except Exception as e:
                logger.error(f"Error processing PubMed article: {e}")
                continue

        if not articles:
            logger.warning("No articles could be processed from PubMed")
        else:
            logger.info(f"Successfully processed {len(articles)} articles from PubMed")

        return articles

    except requests.RequestException as e:
        logger.error(f"Error retrieving data from PubMed: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in PubMed search: {e}")
        return []

#old code without pubmed, PLEASE DON'T DELETE BELOW!
# just in case maguba yawaaaa, ang pubmed feature kay DI JUD MU RETRIEVE , Arxiv ra ang oks AHHAHAHHAHHAHHA
# import requests
# from datetime import datetime
# import logging


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def search_arxiv_articles(query, date_range):
#     """Searches for articles on ArXiv based on the query and date range."""
    
#     start_year, end_year = date_range
#     base_url = "http://export.arxiv.org/api/query"
#     params = {
#         "search_query": query,
#         "start": 0,
#         "max_results": 10,
#         "sortBy": "relevance",
#         "sortOrder": "descending"
#     }

#     try:
#         response = requests.get(base_url, params=params)
#         response.raise_for_status()

#         # Parse XML response
#         import xml.etree.ElementTree as ET
#         root = ET.fromstring(response.content)
        
#         # Define namespaces
#         ns = {
#             'atom': 'http://www.w3.org/2005/Atom',
#             'arxiv': 'http://arxiv.org/schemas/atom'
#         }

#         articles = []
#         for entry in root.findall('atom:entry', ns):
#             try:
#                 title = entry.find('atom:title', ns).text
#                 summary = entry.find('atom:summary', ns).text
#                 published = entry.find('atom:published', ns).text
#                 url = entry.find('atom:id', ns).text
                
#                 # Extract authors
#                 authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                
#                 # Check publication year
#                 published_year = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").year
                
#                 if start_year <= published_year <= end_year:
#                     articles.append({
#                         'title': title,
#                         'summary': summary,
#                         'authors': authors,
#                         'published': published,
#                         'url': url
#                     })
#             except Exception as e:
#                 logger.error(f"Error processing article: {e}")

#         return articles
#     except requests.RequestException as e:
#         logger.error(f"Error retrieving data from ArXiv: {e}")
#         return []
