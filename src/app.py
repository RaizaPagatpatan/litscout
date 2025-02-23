# app.py

import streamlit as st
from datetime import datetime
from chatgpt_functions import get_chatgpt_response
from document_functions import create_word_doc_from_json
from search_function import search_articles
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to the assets directory
current_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(os.path.dirname(current_dir), 'assets')
json_path = os.path.join(assets_dir, 'languages.json')

# try:
#     with open(json_path, 'r') as f:
#         languages_data = json.load(f)
# except FileNotFoundError:
#     st.error(f"Could not find languages file at {json_path}. Using default languages.")
#     languages_data = {
#         "languages": [
#             "English",
#             "Spanish",
#             "French",
#             "German",
#             "Chinese",
#             "Japanese",
#             "Korean"
#         ]
#     }

st.set_page_config(page_title="LitSCOUT", page_icon="📚")
st.title("LitSCOUT")
st.header("Related Literature LLM Tool for Researchers")

# Sidebar for configuration
st.sidebar.header("Research Parameters")

# Input fields
research_topic = st.text_input("Research Topic:", help="Enter the main topic of your research")
related_topic = st.text_input("Related Topic (Optional):", help="Enter a closely related research topic")

# Inputs
col1, col2 = st.columns(2)

with col1:
    field_of_study = st.selectbox(
        "Field of Study:", 
        ["-- Not Specified --", "Physics", "Mathematics", "Biology", "Computer Science", "Chemistry", "Other"],
        help="Choose the primary field of your research"
        
    )
    type_of_publication = st.selectbox(
        "Type of Publication:", 
        ["-- Not Specified --", "Journal Article", "Conference Paper", "Preprint", "Other"],
        help="Select the type of publication you're interested in"
    )

with col2:
    date_range = st.slider(
        "Date Range (Year):", 
        min_value=2000, 
        max_value=datetime.now().year, 
        value=(2000, 2023),
        help="Select the range of publication years"
    )
    citation_format = st.selectbox(
        "Choose Citation Format:", 
        ("APA", "MLA"),
        help="Select the citation style for references"
    )

keywords = st.text_area(
    "Keywords (up to 20, comma-separated):", 
    help="Enter relevant keywords to refine your search")
if keywords:
    keyword_input_list = [item.strip() for item in keywords.split(",") if item.strip()]
    # st.write("Items entered:", keyword_input_list)
else:
    st.write("Enter Items!")

# language_options = languages_data.get("languages", ["-- Not Specified --"])

with st.expander("Advanced Search Options"):
    col1, col2, col3 = st.columns(3)
    with col1:
        open_access_site = st.selectbox(
            "Select Open Access Site",
            [
                "-- Not Specified --", 
                "ArXiv", 
                "PubMed", 
                "OpenAIRE", 
                "Google Scholar"  
            ]
        )
        # authors = st.text_area(
        #     "Author(s)",
        #     help="Input name of preferred author"
        #     )
        # # multiple input list
        # author_input_list = []
        # if authors:
        #     author_input_list = [item.strip() for item in authors.split(",") if item.strip()]
        #     # st.write("Items entered:", author_input_list)
        # else:
        #     st.write("Enter items!")

        # # test
        # if st.button("Show Count"):
        #     st.write(f"Number of items entered: {len(author_input_list)}")
        # else:
        #     st.write("no input")

    # with col2:
    #     citation_count = st.number_input(
    #         "Citation Count",
    #         min_value = 0,
    #         step = 1,
    #         format="%d",
    #         help="Enter the minimum number of citations you want the papers to have")
        # institution = st.text_input(
        #     "Institution",
        #     help="Enter the name of the academic or research institution you want to search for")
        

    # with col3:
    #     language_filter = st.selectbox(
    #         "Language Filter",                     
    #         language_options,
    #         help="Select your preferred language")


# test selection display
st.write(f"Selected Open Access Pub. Site: {open_access_site}")

# Generate button
if st.button("Generate Research Report"):
    if research_topic:
        try:
            with st.spinner('Generating research report...'):
                # Search for articles
                search_results = search_articles(research_topic, date_range, open_access_site)
                logger.info(f"Search results count: {len(search_results)}")
                
                # Save search results to JSON file
                import json
                from datetime import datetime
                import os
                
                try:
                    # Ensure the directory exists
                    json_dir = os.path.join(os.path.dirname(__file__), '..', 'search_results')
                    os.makedirs(json_dir, exist_ok=True)
                    
                    # Create a filename with timestamp and research topic
                    safe_topic = ''.join(c if c.isalnum() or c in [' ', '_'] else '_' for c in research_topic)
                    safe_topic = safe_topic[:50]  # Limit filename length
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_filename = os.path.join(json_dir, f"search_results_{safe_topic}_{timestamp}.json")
                    
                    # Save search results to JSON
                    with open(json_filename, 'w', encoding='utf-8') as f:
                        json.dump(search_results, f, ensure_ascii=False, indent=4)
                    
                    logger.info(f"Saved search results to {json_filename}")
                    logger.info(f"First search result: {search_results[0] if search_results else 'No results'}")
                
                except Exception as e:
                    logger.error(f"Error saving search results to JSON: {e}")
                
                logger.info(f"First few search results: {search_results[:1] if search_results else 'No results'}")
                
                # Generate response
                response = get_chatgpt_response(
                    research_topic, 
                    related_topic, 
                    field_of_study, 
                    type_of_publication, 
                    date_range, 
                    keywords, 
                    citation_format,
                    open_access_site,
                )
                
                # Check if response is empty or invalid
                if not response or not response.get('response'):
                    st.warning("Unable to generate research report. Please try again.")
                    
                    # Provide helpful suggestions
                    suggestions_col1, suggestions_col2 = st.columns(2)
                    
                    with suggestions_col1:
                        st.markdown("#### Modify Search")
                        st.write("- Broaden your keywords")
                        st.write("- Extend the date range")
                        st.write("- Remove specific filters")
                    
                    with suggestions_col2:
                        st.markdown("#### Alternative Actions")
                        st.write("- Try a different database")
                        st.write("- Rephrase your research topic")
                        st.write("- Check spelling")
                    
                    # Option to modify search parameters
                    if st.button("Modify Search Parameters"):
                        st.experimental_rerun()
                    
                    st.stop()
                
                # Display response
                st.subheader("Research Summary")
                st.write(response['response'])
                
                # Create Word doc
                doc_path = create_word_doc_from_json(response)
                
                # Provide download button
                with open(doc_path, "rb") as file:
                    st.download_button(
                        label="Download Research Report",
                        data=file,
                        file_name="research_report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
                st.success("Research report generated successfully!")
        
        except Exception as e:
            # Catch any unexpected errors
            st.error(f"An error occurred: {e}")
            
            # Provide suggestions
            suggestions_col1, suggestions_col2 = st.columns(2)
            
            with suggestions_col1:
                st.markdown("#### Troubleshooting")
                st.write("- Check your internet connection")
                st.write("- Verify API keys are correctly set")
            
            with suggestions_col2:
                st.markdown("#### Alternative Actions")
                st.write("- Try a different research topic")
                st.write("- Restart the application")
            
            # Log the error for debugging
            logger.error(f"Unexpected error in report generation: {e}")
            
            # Option to modify search parameters
            if st.button("Try Again"):
                st.experimental_rerun()
    else:
        st.warning("Please enter a research topic.")

# Research parameters sidebar
st.sidebar.markdown("---")
st.sidebar.info("LitSCOUT helps researchers discover and summarize relevant academic literature.")
st.sidebar.info("Contributors:\n" "\nRAIZA J. PAGATPATAN BS Computer Science, Cebu Institute of Technology- University, raizapagatpatan.ed@gmail.com\n" "\nJETHRO L. CENAS BS Computer Science, Cebu Institute of Technology- University, jethrocenas@gmail.com\n" "\nJUN ALBERT PARDILLO BSCS Adviser, Cebu Institute of Technology- University, pardillo.junalbert@gmail.com")
