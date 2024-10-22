# document_functions.py
from docx import Document

# Function to create a Word document from JSON data
def create_word_doc_from_json(data, filename='output.docx'):
    doc = Document()
    doc.add_heading('Generated Response', 0)
    
    # Add research topic
    doc.add_paragraph(f"Research Topic: {data['research_topic']}")
    
    # Add response summary
    doc.add_paragraph(f"Summary: {data['response']}")
    
    # Add articles in the chosen citation format
    doc.add_heading('Articles', level=1)
    for article in data['articles']:
        if data['citation_format'] == 'APA':
            doc.add_paragraph(
                f"{', '.join(article['authors'])} ({article['published'][:4]}). {article['title']}. Retrieved from ArXiv."
            )
        elif data['citation_format'] == 'MLA':
            doc.add_paragraph(
                f"{', '.join(article['authors'])}. \"{article['title']}\". ArXiv, {article['published'][:4]}, https://arxiv.org."
            )
    
    # Save the document
    doc.save(filename)
    print(f"Document saved as {filename}")
