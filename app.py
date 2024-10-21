# app.py

import streamlit as st
from chatgpt_functions import get_chatgpt_response

# Streamlit App
st.title("LitSCOUT")
st.header("Related Literature LLM Tool for Researchers")

# Content
user_message = st.text_area("Research Topic:")
# mangita sa mga open-source db, tapos i give niya mga context about that single parameter (RAG)

if st.button("Generate Response"):
    if user_message:

        response = get_chatgpt_response(user_message)
        
        st.write("ChatGPT Response:")
        st.write(response)

        # Indicate that a Word document has been generated
        st.success("Word document has been generated (check chatgpt_response.docx).")
    else:
        st.error("Please enter a message.")
