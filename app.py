# app.py

import streamlit as st
from chatgpt_functions import get_chatgpt_response
from datetime import datetime

# Streamlit App
st.title("LitSCOUT")
st.header("Related Literature LLM Tool for Researchers")

# Input for research topic
research_topic = st.text_area("Research Topic:")

# Input for citation format
citation_format = st.selectbox("Choose Citation Format:", ("APA", "MLA"))

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


# Generate response on button click
if st.button("Generate Response"):
    if research_topic:
        response = get_chatgpt_response(research_topic, citation_format)
        
        st.write("Generated Response:")
        st.write(response)

        # Indicate that a Word document has been generated
        st.success(f"Word document has been generated ({research_topic}_{citation_format}_{timestamp}.docx).")
    else:
        st.error("Please enter a research topic.")
