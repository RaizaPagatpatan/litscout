# app.py

import streamlit as st
from datetime import datetime
from chatgpt_functions import get_chatgpt_response
from document_functions import create_word_doc_from_json

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
        ["-- Select --", "Physics", "Mathematics", "Biology", "Computer Science", "Chemistry", "Other"],
        help="Choose the primary field of your research"
    )
    type_of_publication = st.selectbox(
        "Type of Publication:", 
        ["-- Select --", "Journal Article", "Conference Paper", "Preprint", "Other"],
        help="Select the type of publication you're interested in"
    )

with col2:
    date_range = st.slider(
        "Date Range (Year):", 
        min_value=1900, 
        max_value=datetime.now().year, 
        value=(2000, 2023),
        help="Select the range of publication years"
    )
    citation_format = st.selectbox(
        "Choose Citation Format:", 
        ("APA", "MLA"),
        help="Select the citation style for references"
    )

keywords = st.text_area("Keywords (up to 20, comma-separated):", help="Enter relevant keywords to refine your search")

# Generate button
if st.button("Generate Research Report"):
    if research_topic:
        with st.spinner('Generating research report...'):
            try:
                response = get_chatgpt_response(
                    research_topic, 
                    related_topic, 
                    field_of_study, 
                    type_of_publication, 
                    date_range, 
                    keywords, 
                    citation_format
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
