# document_functions.py

import os
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def create_word_doc_from_json(data, filename='output.docx'):
    """
    Creates a Word document from the provided JSON data.
    
    Args:
        data (dict): Dictionary containing research topic, response, and articles
    """
    try:
        # Create a new Word document
        doc = Document()
        
        # Add title
        title = doc.add_heading('Generated Research Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add research topic
        topic_heading = doc.add_heading('Research Topic:', level=1)
        doc.add_paragraph(data['research_topic'])
        
        # Add response
        summary_heading = doc.add_heading('Research Summary:', level=1)
        doc.add_paragraph(data['response'])
        
        # Add related articles
        if data.get('articles', []):
            articles_heading = doc.add_heading('Related Articles:', level=1)
            
            for article in data.get('articles', []):
                # Format authors
                authors = article.get('authors', [])
                if not authors:
                    author_text = "No authors listed"
                elif len(authors) == 1:
                    author_text = authors[0]
                elif len(authors) == 2:
                    author_text = f"{authors[0]} & {authors[1]}"
                else:
                    author_text = f"{authors[0]} et al."
                
                # Extract year from publication date
                pub_date = article.get('published', '')
                try:
                    # Handle string representation of dict
                    if isinstance(pub_date, str) and pub_date.startswith('{'):
                        import ast
                        date_dict = ast.literal_eval(pub_date)
                        pub_date = date_dict.get('$', '')
                    pub_year = pub_date.split('-')[0] if pub_date else 'N/A'
                except:
                    pub_year = 'N/A'
                
                # Format DOI as URL
                doi = article.get('doi', '')
                if doi:
                    doi_url = f"https://doi.org/{doi}"
                else:
                    doi_url = 'N/A'
                
                # Format journal information
                journal_info = []
                if article.get('journal'):
                    journal_info.append(article['journal'])
                if article.get('volume'):
                    journal_info.append(f"Vol. {article['volume']}")
                if article.get('issue'):
                    journal_info.append(f"No. {article['issue']}")
                if article.get('pages'):
                    journal_info.append(f"pp. {article['pages']}")
                journal_text = ', '.join(filter(None, journal_info))
                
                # Create citation based on format
                if data['citation_format'] == 'APA':
                    if journal_text:
                        citation = f"{author_text} ({pub_year}). {article['title']}. {journal_text}. {doi_url}"
                    else:
                        citation = f"{author_text} ({pub_year}). {article['title']}. {doi_url}"
                elif data['citation_format'] == 'MLA':
                    if journal_text:
                        citation = f"{author_text}. \"{article['title']}\". {journal_text}, {pub_year}. {doi_url}"
                    else:
                        citation = f"{author_text}. \"{article['title']}\". {doi_url}, {pub_year}."
                
                doc.add_paragraph(citation)
        
        # Save the document
        doc.save(filename)
        print(f"Document saved successfully as {filename}")
        return filename
    except Exception as e:
        print(f"Error creating document: {str(e)}")
        return False