import streamlit as st
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.graph import create_visualization
from frontend.utils.styles import apply_custom_css

# Page config
st.set_page_config(
    page_title="Materials Usage Analysis",
    page_icon="💹",
    layout="wide"
)

# Apply custom styling
apply_custom_css()

st.title(":chart_with_upwards_trend: Material Usage Analysis")

# Predefined visualization options - match these EXACTLY with backend conditions
viz_options = {
    "Material Usage Trends": "Create a line chart showing total material usage over time",  # This must match exactly
    "Top Materials": "Create a bar chart showing the top 10 materials by Total Length Used",
    "Top Offcuts": "Create a bar chart showing top 10 items by total offcut length",
    "Material Efficiency": "Create a visualization of top and bottom 5 materials by efficiency",
    "Create a Visualisation": None  # Changed to None for custom queries
}

# Visualization selector
selected_viz = st.selectbox(
    "Choose Visualisation Type",
    options=list(viz_options.keys())
)

# Custom query input if selected
if selected_viz == "Create a Visualisation":
    query_prompt = st.text_area(
        "Enter your visualisation query",
        placeholder="Example: Show me bar plots of the monthly trend of materials usage by total length used"
    )
else:
    query_prompt = viz_options[selected_viz]  # This will now match exactly with backend conditions

# Generate visualization button
if st.button("Generate Visualisation"):
    if query_prompt:  # Add check to ensure we have a prompt
        with st.spinner("Generating visualisation..."):
            try:
                fig = create_visualization(query_prompt)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Failed to generate visualisation. Please try a different query.")
            except Exception as e:
                st.error(f"Error generating visualisation: {str(e)}")
