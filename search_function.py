# search_function.py

import requests
from datetime import datetime
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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