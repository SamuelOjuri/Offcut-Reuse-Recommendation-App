import streamlit as st
import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.chat_agent import stream_final_answer
from utils.styles import apply_custom_css

# Set page config
st.set_page_config(
    page_title="Materials Usage Chat Assistant", 	
    page_icon=":ice_cube:",
    layout="wide"
)

# Apply custom CSS
apply_custom_css()

# Add title and description
st.title(":ice_cube: Materials Usage Chat Assistant")
st.markdown("""
    Ask questions about your **materials usage database** and get answers in natural language.
    The assistant will automatically generate answers to your queries...
""")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Get the current file's directory (frontend folder)
current_dir = Path(__file__).parent

# Define image paths relative to the frontend directory
user_avatar = str(current_dir / 'assets' / 'user.png')
assistant_avatar = str(current_dir / 'assets' / 'chatbot.png')

# Display chat history
for message in st.session_state.messages:
    # Set appropriate avatar based on the role
    avatar = user_avatar if message["role"] == "user" else assistant_avatar
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your database..."):
    # Display user message
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(prompt)
    
    # Add user message to chat history 
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt
    })
    
    # Display assistant response
    with st.chat_message("assistant", avatar=assistant_avatar):
        with st.spinner("Generating answer..."):
            response = st.write_stream(stream_final_answer(prompt))
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response
            })

# Add a button to clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()
