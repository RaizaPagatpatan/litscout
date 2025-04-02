# import logging
# import scholarly
# from typing import List, Dict, Union
# from datetime import datetime, timedelta

# logger = logging.getLogger(__name__)

# def parse_publication_year(pub_year):
#     """
#     Safely parse publication year from various possible formats.
    
#     Args:
#         pub_year: Publication year from scholarly library
    
#     Returns:
#         int: Parsed year or current year if parsing fails
#     """
#     try:
#         # Handle different possible year formats
#         if isinstance(pub_year, (int, float)):
#             return int(pub_year)
#         elif isinstance(pub_year, str):
#             return int(pub_year)
#         elif isinstance(pub_year, tuple):
#             # If it's a tuple, try to extract the first numeric value
#             for item in pub_year:
#                 try:
#                     return int(item)
#                 except (ValueError, TypeError):
#                     continue
        
#         # If all parsing fails, return current year
#         return datetime.now().year
    
#     except Exception as e:
#         logger.warning(f"Could not parse publication year: {pub_year}. Error: {e}")
#         return datetime.now().year

# def parse_date_range(date_range):
#     """
#     Parse date range to extract start year.
    
#     Args:
#         date_range (int or tuple): Date range to filter publications
    
#     Returns:
#         int: Start year for filtering publications
#     """
#     try:
#         current_year = datetime.now().year
        
#         # If it's an integer, calculate start year by subtracting from current year
#         if isinstance(date_range, int):
#             return current_year - date_range
        
#         # If it's a tuple, try to extract the start year
#         elif isinstance(date_range, tuple):
#             # If tuple has two elements (start_year, end_year)
#             if len(date_range) == 2:
#                 return date_range[0]
#             # If tuple has one element, treat it like an integer
#             elif len(date_range) == 1:
#                 return current_year - date_range[0]
        
#         # If parsing fails, return current year minus 5 as default
#         return current_year - 5
    
#     except Exception as e:
#         logger.warning(f"Could not parse date range: {date_range}. Error: {e}")
#         return datetime.now().year - 5

# def search_google_scholar_articles(query: str, date_range: Union[int, tuple]) -> List[Dict]:
#     """
#     Search Google Scholar for academic articles and extract key information.
    
#     Args:
#         query (str): Search query for Google Scholar
#         date_range (int or tuple): Number of years or specific year range to search
    
#     Returns:
#         List[Dict]: List of dictionaries containing article metadata
#     """
#     try:
#         # Log the query safely
#         logger.info(f"Searching Google Scholar with query: {query}")
        
#         # Parse date range to get start year
#         start_year = parse_date_range(date_range)

#         # Initialize results list
#         scholar_results = []

#         # Use scholarly to search publications with robust method selection
#         search_methods = [
#             scholarly.search_pubs,  # Primary method
#             getattr(scholarly, 'search_publication', None),  # Alternative method
#             getattr(scholarly, 'search', None)  # Fallback method
#         ]

#         search_query = None
#         for method in search_methods:
#             if method is not None:
#                 try:
#                     search_query = scholarly.search_pubs(query)
#                     response = next(search_query)
#                     break
#                 except Exception as e:
#                     logging.warning(f"Failed to use method {method.__name__}: {e}")

#         if search_query is None:
#             raise AttributeError("No suitable search method found in scholarly library")

#         # Limit results and filter by year
#         for i, pub in enumerate(search_query):
#             if i >= 20:  # Limit to 20 results
#                 break

#             try:
#                 # Fill publication details to get more information
#                 pub = scholarly.fill(pub)
#             except Exception as e:
#                 logging.warning(f"Could not fill publication details: {e}")
#                 continue

#             # Parse publication year and apply date range filter
#             pub_year = parse_publication_year(pub.get('bib', {}).get('pub_year', datetime.now().year))
            
#             if isinstance(date_range, int):
#                 if pub_year < (datetime.now().year - date_range):
#                     continue
#             elif isinstance(date_range, tuple):
#                 start_year, end_year = date_range
#                 if pub_year < start_year or pub_year > end_year:
#                     continue

#             # Extract key publication information
#             scholar_result = {
#                 'title': pub.get('bib', {}).get('title', 'N/A'),
#                 'authors': pub.get('bib', {}).get('author', []),
#                 'year': pub_year,
#                 'venue': pub.get('bib', {}).get('venue', 'N/A'),
#                 'abstract': pub.get('bib', {}).get('abstract', 'N/A'),
#                 'citations': pub.get('num_citations', 0),
#                 'url': pub.get('pub_url', 'N/A')
#             }
#             scholar_results.append(scholar_result)

#         logger.info(f"Found {len(scholar_results)} Google Scholar articles")
#         return scholar_results

#     except Exception as e:
#         logger.error(f"Google Scholar search error: {e}", exc_info=True)
#         return []