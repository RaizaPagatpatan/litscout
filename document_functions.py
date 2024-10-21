# document_functions.py
from docx import Document
import json

# JSON formatted doxc function
def create_word_doc_from_json(data, filename='output.docx'):
    doc = Document()
    doc.add_heading('ChatGPT Response', 0)

    # Add content from the JSON
    for key, value in data.items():
        doc.add_paragraph(f"{key}: {value}")
    
    doc.save(filename)
    print(f"Document saved as {filename}")
