# search_functions.py

import requests

# Function to search ArXiv API for articles on a specific topic
def search_arxiv_articles(research_topic):
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{research_topic}",
        "start": 0,
        "max_results": 5,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.text
        
        # Parse the ArXiv API XML response (example of data extraction)
        articles = []
        entries = data.split("<entry>")[1:]  # Simplified XML parsing
        for entry in entries:
            title = entry.split("<title>")[1].split("</title>")[0].strip()
            summary = entry.split("<summary>")[1].split("</summary>")[0].strip()
            authors = [a.split("</name>")[0] for a in entry.split("<name>")[1:]]
            published = entry.split("<published>")[1].split("</published>")[0]
            articles.append({
                'title': title,
                'summary': summary,
                'authors': authors,
                'published': published
            })
        
        return articles
    
    except requests.RequestException as e:
        print(f"Error retrieving data from ArXiv: {e}")
        return []
