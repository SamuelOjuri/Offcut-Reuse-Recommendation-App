import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import func

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.app import db, app
from backend.models import BatchItem, Item, Offcut
from frontend.utils.styles import apply_custom_css

# Page config
st.set_page_config(
    page_title="Material Reports",
    page_icon="📊",
    layout="wide"
)

# Apply custom styling
apply_custom_css()

st.title("📊 Materials Usage Reports")

# Create tabs for different report views
tab1, tab2, tab3 = st.tabs(["Summary Metrics", "Available Offcuts", "Detailed Analysis"])

with tab1:
    # Create Flask application context
    with app.app_context():
        # Query to get summary metrics by item description
        query = db.session.query(
            Item.item_description,
            func.sum(BatchItem.input_bar_length_mm * BatchItem.quantity).label('total_input_length'),
            func.sum(BatchItem.total_length_used_mm).label('total_used_length'),
            func.sum(BatchItem.total_offcut_length_created_mm).label('total_offcut_length'),
            func.avg(BatchItem.usage_efficiency).label('avg_efficiency'),
            func.avg(BatchItem.waste_percentage).label('avg_waste')
        ).join(BatchItem).group_by(Item.item_description).all()
    
    # Convert to DataFrame
    df = pd.DataFrame(query, columns=[
        'Item Description', 
        'Total Input Length (mm)', 
        'Total Used Length (mm)',
        'Total Offcut Length (mm)',
        'Average Efficiency (%)',
        'Average Waste (%)'
    ])
    
    # Convert Decimal to float before rounding
    df['Average Efficiency (%)'] = df['Average Efficiency (%)'].astype(float).round(2)
    df['Average Waste (%)'] = df['Average Waste (%)'].astype(float).round(2)
    
    # Display metrics in columns - convert mm to m by dividing by 1000
    total_input = df['Total Input Length (mm)'].sum() / 1000
    total_used = df['Total Used Length (mm)'].sum() / 1000
    total_offcut = df['Total Offcut Length (mm)'].sum() / 1000
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Input Length", f"{total_input:,.1f} m")
    with col2:
        st.metric("Total Used Length", f"{total_used:,.1f} m")
    with col3:
        st.metric("Total Offcut Length", f"{total_offcut:,.1f} m")
    
    # Display the full table with sorting
    st.dataframe(
        df,
        column_config={
            "Item Description": st.column_config.TextColumn(width="large"),
            "Total Input Length (mm)": st.column_config.NumberColumn(format="%d"),
            "Total Used Length (mm)": st.column_config.NumberColumn(format="%d"),
            "Total Offcut Length (mm)": st.column_config.NumberColumn(format="%d"),
            "Average Efficiency (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Average Waste (%)": st.column_config.NumberColumn(format="%.2f%%")
        },
        hide_index=True
    )

with tab2:
    st.subheader("🔍 Available Offcuts Inventory")
    
    with app.app_context():
        # Query available offcuts
        offcuts = db.session.query(
            Offcut.material_profile,
            Offcut.length_mm,
            func.count(Offcut.offcut_id).label('quantity')
        ).filter(
            Offcut.is_available == True
        ).group_by(
            Offcut.material_profile,
            Offcut.length_mm
        ).order_by(
            Offcut.material_profile,
            Offcut.length_mm.desc()
        ).all()
        
        # Convert to DataFrame
        offcuts_df = pd.DataFrame(offcuts, columns=[
            'Material Profile',
            'Length (mm)',
            'Quantity Available'
        ])
        
        # Get unique material profiles for filtering
        material_profiles = ['All'] + sorted(offcuts_df['Material Profile'].unique().tolist())
        
        # Add a filter for material profiles
        selected_profile = st.selectbox(
            "Filter by Material Profile",
            options=material_profiles
        )
        
        # Filter the dataframe based on selection
        if selected_profile != 'All':
            filtered_df = offcuts_df[offcuts_df['Material Profile'] == selected_profile]
        else:
            filtered_df = offcuts_df
        
        # Display metrics
        total_offcuts = filtered_df['Quantity Available'].sum()
        unique_lengths = filtered_df['Length (mm)'].nunique()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Available Offcuts", f"{total_offcuts:,}")
        with col2:
            st.metric("Unique Lengths", f"{unique_lengths:,}")
        
        # Display the filtered table
        st.dataframe(
            filtered_df,
            column_config={
                "Material Profile": st.column_config.TextColumn(width="medium"),
                "Length (mm)": st.column_config.NumberColumn(format="%d"),
                "Quantity Available": st.column_config.NumberColumn(format="%d")
            },
            hide_index=True
        )
        
        # Add a download button for the filtered data
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Offcuts Data",
            data=csv,
            file_name=f"offcuts_inventory_{selected_profile.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )

with tab3:
    st.info("Detailed analysis features coming soon!")
