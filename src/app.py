# app.py

import streamlit as st
from datetime import datetime
from chatgpt_functions import get_chatgpt_response
from document_functions import create_word_doc_from_json
import json

json_path = "assets\languages.json"

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
    st.write("Items entered:", keyword_input_list)
else:
    st.write("Enter Items!")


# Load language options from JSON file
try:
    with open(json_path, "r", encoding="utf-8") as file:
        language_data = json.load(file)
        language_options = language_data.get("languages", ["-- Not Specified --"])
except Exception as e:
    st.error(f"Error loading languages: {e}")
    language_options = ["-- Not Specified --"]

# additional_search = st.text("Advanced settings >>")
with st.expander("Advanced Search Options"):
    col1, col2, col3 = st.columns(3)
    with col1:
        open_access_site = st.selectbox(
            "Open Access Publication Site:",
            ["ArXiv", "Semantic Scholar", "PubMed", "OpenAIRE"],
            help="Select the citation style for references"
        )
        authors = st.text_area(
            "Author(s)",
            help="Input name of preferred author"
            )
        # multiple input list
        author_input_list = []
        if authors:
            author_input_list = [item.strip() for item in authors.split(",") if item.strip()]
            st.write("Items entered:", author_input_list)
        else:
            st.write("Enter items!")

        # test
        if st.button("Show Count"):
            st.write(f"Number of items entered: {len(author_input_list)}")
        else:
            st.write("no input")

    with col2:
        citation_count = st.number_input(
            "Citation Count",
            min_value = 0,
            step = 1,
            format="%d",
            help="Enter the minimum number of citations you want the papers to have")
        institution = st.text_input(
            "Institution",
            help="Enter the name of the academic or research institution you want to search for")
        

    with col3:
        language_filter = st.selectbox(
            "Language Filter",                     
            # ["-- Not Specified --", "English", "Filipino", "French", "Korean"],
            # insert json later,
            language_options,
            help="Select your preferred language")


# test selection display
st.write(f"Selected Open Access Pub. Site: {open_access_site}")

# Generate button
if st.button("Generate Research Report"):
    if research_topic:
        with st.spinner('Generating research report...'):
            try:
                print("Open Access Site:", open_access_site)
                response = get_chatgpt_response(
                    research_topic, 
                    related_topic, 
                    field_of_study, 
                    type_of_publication, 
                    date_range, 
                    keywords, 
                    citation_format,
                    open_access_site,
                    # citation_count,
                    # institution,
                    # language_filter
                )
                
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
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a research topic.")

# Research parameters sidebar
st.sidebar.markdown("---")
st.sidebar.info("LitSCOUT helps researchers discover and summarize relevant academic literature.")
st.sidebar.info("Contributors:\n" "\nRAIZA J. PAGATPATAN BS Computer Science, Cebu Institute of Technology- University, raizapagatpatan.ed@gmail.com\n" "\nJETHRO L. CENAS BS Computer Science, Cebu Institute of Technology- University, jethrocenas@gmail.com")
