# search_function.py

import requests
from datetime import datetime
import logging
import time
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from scrape_functions import search_google_scholar_articles

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
        print("Searching PubMed...")
        return search_pubmed_articles(query, date_range)
    elif open_access_site.lower() == "openaire":
        print("Searching OpenAIRE...")
        return search_openaire_articles(query, date_range)
    elif open_access_site.lower() == "google scholar":
        print("Searching Google Scholar...")
        return search_google_scholar_articles(query, date_range)
    else:
        logger.error(f"Unsupported database: {open_access_site}")
        return []

def search_arxiv_articles(
    query, date_range):
    """Searches for articles on ArXiv based on the query and date range."""
    
    start_year, end_year = date_range
    logger.info(f"Searching ArXiv with query: {query}")
    logger.info(f"Date range: {start_year} - {end_year}")
    
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": 10,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    try:
        logger.info(f"Sending request to ArXiv with params: {params}")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        logger.info(f"Received response from ArXiv. Status code: {response.status_code}")
        
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
                    article = {
                        'title': title,
                        'summary': summary,
                        'authors': authors,
                        'published': published,
                        'url': url
                    }
                    articles.append(article)
                    logger.info(f"Added article: {title}")
            except Exception as e:
                logger.error(f"Error processing article: {e}")
        
        logger.info(f"Total articles found: {len(articles)}")
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
            "retmax": 20,  
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

def search_openaire_articles(query, date_range):
    """
    Searches for articles on OpenAIRE based on the query and date range.
    Returns formatted articles suitable for vector store creation.
    """
    try:
        logger.info(f"Searching OpenAIRE for: {query}")
        base_url = "https://api.openaire.eu/search/publications"
        
        # Format date range for OpenAIRE API
        start_year, end_year = date_range
        from_date = f"{start_year}-01-01"
        to_date = f"{end_year}-12-31"
        
        # Clean up query
        keywords = query.replace('Journal Article', '').strip()
        
        # Start with minimal parameters
        params = {
            'keywords': keywords,
            'format': 'json',
            'size': 10
        }
        
        # Only add date parameters if they're within a reasonable range
        if int(start_year) >= 1900:
            params['fromDateAccepted'] = from_date
        if int(end_year) <= 2025:
            params['toDateAccepted'] = to_date
        
        logger.info(f"Making request to OpenAIRE with URL: {base_url}")
        logger.info(f"Request parameters: {params}")
        
        response = requests.get(base_url, params=params)
        
        # Log the actual URL being called for debugging
        logger.info(f"Full URL being called: {response.url}")
        
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response data type: {type(data)}")
        logger.info(f"Response data keys: {data.keys() if isinstance(data, dict) else 'Not a dictionary'}")
        
        articles = []
        
        # Check if we have a valid response structure
        if isinstance(data, dict) and 'response' in data:
            response_data = data['response']
            if 'results' in response_data:
                results = response_data['results']
                if isinstance(results, dict) and 'result' in results:
                    results_list = results['result']
                    if not isinstance(results_list, list):
                        results_list = [results_list]
                    
                    logger.info(f"Number of results found: {len(results_list)}")
                    
                    for result in results_list:
                        try:
                            if not isinstance(result, dict):
                                continue
                            
                            metadata = result.get('metadata', {})
                            if not metadata:
                                continue
                                
                            oaf_entity = metadata.get('oaf:entity', {})
                            if not oaf_entity:
                                continue
                                
                            oaf_result = oaf_entity.get('oaf:result', {})
                            if not oaf_result:
                                continue
                            
                            # Extract title
                            title = ''
                            title_data = oaf_result.get('title', [])
                            if title_data and isinstance(title_data, list):
                                title = title_data[0].get('$', '') if isinstance(title_data[0], dict) else str(title_data[0])
                            
                            # Extract abstract
                            abstract = ''
                            description_data = oaf_result.get('description', [])
                            if description_data and isinstance(description_data, list):
                                abstract = description_data[0].get('$', '') if isinstance(description_data[0], dict) else str(description_data[0])
                            
                            # Extract authors
                            authors = []
                            creator_data = oaf_result.get('creator', [])
                            if creator_data and isinstance(creator_data, list):
                                for creator in creator_data:
                                    if isinstance(creator, dict):
                                        author_name = creator.get('$', '')
                                        if author_name:
                                            authors.append(author_name)
                            
                            # Extract DOI
                            doi = ''
                            pid_data = oaf_result.get('pid', [])
                            if pid_data and isinstance(pid_data, list):
                                for pid in pid_data:
                                    if isinstance(pid, dict) and pid.get('@classid') == 'doi':
                                        doi = pid.get('$', '')
                                        break
                            
                            # Extract publication date (try multiple fields)
                            pub_date = ''
                            for date_field in ['dateofacceptance', 'publicationdate', 'year']:
                                date_data = oaf_result.get(date_field, [])
                                if date_data:
                                    if isinstance(date_data, list):
                                        date_value = date_data[0].get('$', '') if isinstance(date_data[0], dict) else str(date_data[0])
                                    else:
                                        date_value = str(date_data)
                                    
                                    # If date is a string representation of a dict, try to parse it
                                    if isinstance(date_value, str) and date_value.startswith('{'):
                                        try:
                                            import ast
                                            date_dict = ast.literal_eval(date_value)
                                            date_value = date_dict.get('$', '')
                                        except:
                                            pass
                                    
                                    if date_value:
                                        pub_date = date_value
                                        break
                            
                            # Extract journal information
                            journal = ''
                            journal_data = oaf_result.get('journal', [])
                            if journal_data and isinstance(journal_data, list):
                                journal = journal_data[0].get('$', '') if isinstance(journal_data[0], dict) else str(journal_data[0])
                            
                            # Extract volume and issue
                            volume = ''
                            volume_data = oaf_result.get('volume', [])
                            if volume_data and isinstance(volume_data, list):
                                volume = volume_data[0].get('$', '') if isinstance(volume_data[0], dict) else str(volume_data[0])
                            
                            issue = ''
                            issue_data = oaf_result.get('issue', [])
                            if issue_data and isinstance(issue_data, list):
                                issue = issue_data[0].get('$', '') if isinstance(issue_data[0], dict) else str(issue_data[0])
                            
                            # Extract pages
                            pages = ''
                            pages_data = oaf_result.get('pages', [])
                            if pages_data and isinstance(pages_data, list):
                                pages = pages_data[0].get('$', '') if isinstance(pages_data[0], dict) else str(pages_data[0])
                            
                            article = {
                                'title': title.strip(),
                                'authors': [author.strip() for author in authors if author.strip()],
                                'abstract': abstract.strip(),
                                'doi': doi.strip(),
                                'publication_date': str(pub_date).strip(),
                                'journal': journal.strip(),
                                'volume': volume.strip(),
                                'issue': issue.strip(),
                                'pages': pages.strip(),
                                'source': 'OpenAIRE'
                            }
                            
                            # Only add articles that have at least a title or abstract
                            if article['title'] or article['abstract']:
                                articles.append(article)
                        
                        except Exception as e:
                            logger.warning(f"Error processing individual result: {str(e)}")
                            continue
        
        logger.info(f"Successfully processed {len(articles)} articles from OpenAIRE")
        return articles
        
    except requests.RequestException as e:
        logger.error(f"Error retrieving data from OpenAIRE: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in OpenAIRE search: {str(e)}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

#would you be able to add a search function on openaire OPENAIRE_API_KEY is the env variable

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
