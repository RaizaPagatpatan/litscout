# document_functions.py

import os
from docx import Document
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_word_doc_from_json(data, filename='output.docx'):
    print("Data received for document creation:", data)  # Add this line
    print("Articles in data:", data.get('articles', []))  # Add this line
    """Creates a Word document with data and enhanced response."""
    doc = Document()
    doc.add_heading('Generated Research Report', 0)

    # Research details
    doc.add_paragraph(f"Research Topic: {data['research_topic']}")
    doc.add_paragraph(f"Field of Study: {data.get('field_of_study', 'Not Specified')}")
    doc.add_paragraph(f"Publication Type: {data.get('type_of_publication', 'Not Specified')}")

    # Generated response section
    doc.add_heading('Research Summary', level=1)
    doc.add_paragraph(data['response'])

    # Add articles via chosen citation format
    doc.add_heading('Related Articles', level=1)
    for article in data.get('articles', []):
        # Get publication year, with fallback
        pub_year = "N/A"
        if 'published' in article:
            # Handle different date formats
            pub_date = article['published']
            if isinstance(pub_date, str):
                # Try to extract year from various date formats
                if len(pub_date) >= 4:  # At least contains a year
                    pub_year = pub_date[:4]
        
        authors = article.get('authors', 'Unknown Author')
        if isinstance(authors, list):
            authors = ', '.join(authors)
        
        if data['citation_format'] == 'APA':
            citation = f"{authors} ({pub_year}). {article['title']}. Retrieved from {article.get('url', 'N/A')}."
        elif data['citation_format'] == 'MLA':
            citation = f"{authors}. \"{article['title']}\". {article.get('url', 'N/A')}, {pub_year}."
        doc.add_paragraph(citation)

    # Save the document
    doc.save(filename)
    print(f"Document saved successfully as {filename}")
    return filename