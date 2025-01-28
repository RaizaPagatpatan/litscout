# search_function.py

import requests
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def search_articles(query, date_range, open_access_site):
    """
    Search articles based on selected database
    """
    if open_access_site.lower() == "arxiv":
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
    """Searches for articles on PubMed based on the query."""
    start_year, end_year = date_range
    pubmed_api_key = os.getenv("PUBMED_API_KEY")
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    if not pubmed_api_key:
        logger.error("PUBMED_API_KEY not found in environment variables")
        return []
    
    try:
        # Format query properly for PubMed syntax
        # Remove any special characters and format the date range correctly
        sanitized_query = query.replace('"', '').replace('[', '').replace(']', '')
        formatted_query = f'({sanitized_query}) AND ("{start_year}"[Date - Publication] : "{end_year}"[Date - Publication])'
        
        logger.info(f"Formatted PubMed query: {formatted_query}")
        
        # First, search for article IDs
        search_params = {
            "db": "pubmed",
            "term": formatted_query,
            "retmax": 10,
            "api_key": pubmed_api_key,
            "retmode": "json"
        }
        
        search_url = f"{base_url}/esearch.fcgi"
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()
        
        search_data = search_response.json()
        logger.info(f"PubMed search response: {search_data}")
        
        # Get article IDs
        article_ids = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not article_ids:
            logger.warning(f"No article IDs found for query: {formatted_query}")
            return []
        
        # Fetch detailed information for found articles
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(article_ids),
            "retmode": "xml",
            "api_key": pubmed_api_key
        }
        
        fetch_url = f"{base_url}/efetch.fcgi"
        fetch_response = requests.get(fetch_url, params=fetch_params)
        fetch_response.raise_for_status()
        
        # Parse XML response
        import xml.etree.ElementTree as ET
        root = ET.fromstring(fetch_response.content)
        articles = []
        
        for article in root.findall(".//PubmedArticle"):
            try:
                # Extract article data
                article_data = {}
                
                # Get title
                title_elem = article.find(".//ArticleTitle")
                article_data['title'] = title_elem.text if title_elem is not None else "No title available"
                
                # Get abstract
                abstract_elem = article.find(".//Abstract/AbstractText")
                article_data['summary'] = abstract_elem.text if abstract_elem is not None else "No abstract available"
                
                # Get authors
                authors = []
                author_list = article.findall(".//Author")
                for author in author_list:
                    lastname = author.find(".//LastName")
                    firstname = author.find(".//ForeName")
                    if lastname is not None:
                        author_name = lastname.text
                        if firstname is not None:
                            author_name = f"{lastname.text}, {firstname.text}"
                        authors.append(author_name)
                
                article_data['authors'] = authors if authors else ["Unknown Author"]
                
                # Get publication date
                pub_date = article.find(".//PubDate")
                if pub_date is not None:
                    year = pub_date.find("Year")
                    month = pub_date.find("Month")
                    day = pub_date.find("Day")
                    
                    year_text = year.text if year is not None else "0000"
                    month_text = month.text if month is not None else "01"
                    day_text = day.text if day is not None else "01"
                    
                    article_data['published'] = f"{year_text}-{month_text}-{day_text}"
                else:
                    article_data['published'] = "0000-01-01"
                
                # Get URL
                pmid = article.find(".//PMID")
                article_data['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid.text}/" if pmid is not None else ""
                
                articles.append(article_data)
                
            except Exception as e:
                logger.error(f"Error processing PubMed article: {e}")
                continue
        
        if not articles:
            logger.warning("No articles could be processed from PubMed")
        else:
            logger.info(f"Successfully processed {len(articles)} articles")
            
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


