import streamlit as st
import requests
from typing import Dict, Any
import sys
from pathlib import Path
from frontend.utils.styles import apply_custom_css
import pandas as pd

# Add the project root directory to Python path (if needed)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Page config
st.set_page_config(
    page_title="Offcut Recommender",
    page_icon=":recycle:",
    layout="wide"
)

# Apply custom CSS
apply_custom_css()

def start_recommendation(batch_code: str) -> Dict[Any, Any]:
    """Call the recommendation start endpoint"""
    url = "http://localhost:5000/api/recommendations/start"
    payload = {"batch_code": batch_code}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling recommendation API: {str(e)}")
        return None

def format_batch_code(code: str) -> str:
    """Format the batch code to standard format (BO003643)"""
    # Remove any whitespace and convert to uppercase
    code = code.strip().upper()
    
    # If only numbers provided, add BO prefix and pad with zeros
    if code.isdigit():
        code = f"BO{code.zfill(6)}"
    # If BO prefix is missing, add it and pad the numbers
    elif code.isdigit() and len(code) <= 6:
        code = f"BO{code.zfill(6)}"
    
    return code

def is_valid_batch_code(code: str) -> bool:
    """Validate the batch code format"""
    # Check if the code matches the format: BO followed by 6 digits
    if len(code) == 8 and code.startswith("BO") and code[2:].isdigit():
        return True
    return False

def check_batch_exists(batch_code: str) -> bool:
    """Check if the batch code exists in the database"""
    url = f"http://localhost:5000/api/batches/check/{batch_code}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('exists', False)
    except requests.exceptions.RequestException as e:
        st.error(f"Error checking batch code: {str(e)}")
        return False

# Main content
st.title(":recycle: Offcut Reuse Recommendation System")

st.markdown("""
    Get intelligent recommendations for reusing offcuts based on your batch requirements.
""")

# Input for batch code with validation
batch_code = st.text_input("Enter Batch Code:", 
                          placeholder="e.g., BO003643 or just 3643")

if batch_code:
    # Format the batch code
    formatted_batch_code = format_batch_code(batch_code)
    
    # Validate the formatted code
    if not is_valid_batch_code(formatted_batch_code):
        st.error("Invalid batch code format. Please use format 'BO003643' or just '3643'")
        batch_code = None
    else:
        # Check if batch exists in database
        if not check_batch_exists(formatted_batch_code):
            st.error(f"Batch code {formatted_batch_code} not found in database")
            batch_code = None
        else:
            # If the formatted code is different from input, show the conversion
            if formatted_batch_code != batch_code:
                st.info(f"Batch code formatted to: {formatted_batch_code}")
            batch_code = formatted_batch_code

if st.button("Get Recommendations", icon=":material/recommend:"):
    if not batch_code:
        st.warning("Please enter a valid batch code")
    else:
        with st.spinner("Generating recommendations..."):
            result = start_recommendation(batch_code)
            
        if result:
            st.success(result.get('message', 'Recommendations generated!'))
            
            recommendations = result.get('recommendations', [])
            if recommendations:
                st.subheader("Recommended Offcuts")
                
                # Convert recommendations to DataFrame and reorder columns
                df = pd.DataFrame(recommendations)
                
                # Define column names mapping
                column_names = {
                    'is_double_cut': 'Double Cut',
                    'matched_profile': 'Matched Profile',
                    'legacy_offcut_id': 'Offcut ID',
                    'related_legacy_offcut_id': 'Related Offcut ID',
                    'reasoning': 'Reasoning',
                    'suggested_length': 'Suggested Length (mm)'
                }
                
                # Rename and reorder columns
                df = df.rename(columns=column_names)[list(column_names.values())]

                            
                # Display the DataFrame
                st.dataframe(df, column_config={
                    'Offcut ID': st.column_config.TextColumn(width=None),
                    'Related Offcut ID': st.column_config.TextColumn(width=None),
                    'Suggested Length (mm)': st.column_config.NumberColumn(format="%d")
                }, use_container_width=True)
                
                # Display expandable JSON details
                st.subheader("Detailed Recommendations")
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"Recommendation {i}"):
                        st.json(rec)
                
                # Create columns for buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Recommendations",
                        data=csv,
                        file_name=f"recommendations_{batch_code}.csv",
                        mime="text/csv",
                        help="Download recommendations as CSV file"
                    )

                with col2:
                    if st.button("Confirm Selected Recommendations"):
                        st.info("Confirmation functionality to be implemented")

            else:
                st.info("No recommendations found for this batch")
