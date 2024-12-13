import streamlit as st

def load_css():
    return """
    <style>
       
        
        /* Chat container styling */
        .stChatMessage {
            background-color: var(--secondary-background-color);
            border-radius: 10px;
            padding: 15px;
            margin: 5px 0;
        }

        /*  
        /* User message styling */
        .stChatMessage [data-testid="StyledMessage"] {
            background-color: #2E3440;
            color: #FFFFFF;
        }
        
        /* Assistant message styling */
        .stChatMessage [data-testid="StyledMessage"][data-type="assistant"] {
            background-color: #3B4252;
        }
        */

        div[data-testid="stChatMessageContent"] {
        background-color: #dcdfe6;
        color: black; # Expander content color
        } 
        
        div[data-testid="stChatMessage"] {
            background-color: #dcdfe6;
            color: black; # Adjust this for expander header color
        }
       

        
        
        /* Input box styling */
        
        .stChatInput {
            border-radius: 10px;
            border: 1px solid #5E81AC;
        }

        .stChatInput:focus-within {
            border: none;
            box-shadow: 0 0 0 0.5px #5E81AC;
        }

        /*

        .stTextInput {
            border-radius: 10px;
            outline: none;
            border-color: #5E81AC;     
        }

        .stTextInput:focus-within {
            border: none;
            box-shadow: 0 0 0 1px #5E81AC;
        }

        .stTextInput>div>div>div, .stTextInput>div>div, .stTextInput>div>div>div>input, .stTextInput>div>div>input {
            border-radius: 10px;
            outline: none;
            border: 1px solid #5E81AC;
        }

        */

        /* Target the child element of stTextInput */

        
        .stTextInput>div>div>input {
            border-radius: 10px;
            outline: none;
            border: 1px solid #5E81AC;
        }

        /* Add a focus effect to the input box */
        .stTextInput>div>div>input:focus-within {
            border: none;
            box-shadow: 0 0 0 2px #5E81AC;
        }

            
        /* Spinner styling */
        .stSpinner > div {
            border-color: #7792E3 !important;
        }
        
        /* Clear button styling */
        .stButton button {
            background-color: #4C566A;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 5px 15px;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover {
            background-color: #5E81AC;
            color: white;
        }
        
        /* Avatar container */
        .stChatMessage [data-testid="UserAvatar"],
        .stChatMessage [data-testid="AssistantAvatar"] {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            overflow: hidden;
        }
        
        /* Download button specific styling */
        .stDownloadButton button {
            background-color: #5E81AC !important;  /* Matches your theme primaryColor */
            color: white !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            border-radius: 5px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
            margin: 0.25rem 0 !important;
        }
        
        .stDownloadButton button:hover {
            background-color: #81A1C1 !important;  /* Lighter shade for hover */
            box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
            transform: translateY(-1px) !important;
        }

    </style>
    """

def apply_custom_css():
    st.markdown(load_css(), unsafe_allow_html=True) 