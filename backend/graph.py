import os
from pandasai import SmartDataframe
from langchain_openai import ChatOpenAI
from pandasai.llm import LangchainLLM
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from backend.chat_agent import llm, DATABASE_URL
#from backend.chat_agent import DATABASE_URL  # Import your existing LLM and DB connection
from datetime import datetime, timedelta

# from dotenv import load_dotenv
# load_dotenv()

# openai_api_key = os.getenv("OPENAI_API_KEY")

# llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)  # Example: Replace 'gpt-4' with your desired model


def get_materials_data(force_refresh=False):
    """Get materials data from cache or database"""
    cache_file = "cache/materials_data.csv"
    cache_max_age = timedelta(hours=24)  # Cache expires after 24 hours
    
    # Create cache directory if it doesn't exist
    os.makedirs('cache', exist_ok=True)
    
    # Check if cache exists and is fresh
    if not force_refresh and os.path.exists(cache_file):
        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < cache_max_age:
            return pd.read_csv(cache_file, parse_dates=['batch_date'])
    
    # Define the query
    query = """
        SELECT 
            b.batch_code,
            b.batch_date,
            bd.saw_name,
            i.item_code,
            i.item_description,
            bi.double_cut,
            bi.quantity,
            bi.input_bar_length_mm as input_bar_length,
            (bi.quantity * bi.input_bar_length_mm) as total_input_length,
            bi.bar_length_used_mm as bar_length_used,
            bi.total_length_used_mm as total_length_used,
            bi.offcut_length_created_mm as offcut_length_created,
            bi.total_offcut_length_created_mm as total_offcut_length_created,
            bi.usage_efficiency,
            bi.waste_percentage
        FROM batches b
        JOIN batch_details bd ON b.batch_id = bd.batch_id
        JOIN batch_items bi ON b.batch_id = bi.batch_id
        JOIN items i ON bi.item_id = i.item_id
        ORDER BY b.batch_date DESC
    """
    
    # Create engine and connect to database
    engine = create_engine(DATABASE_URL)
    try:
        # Use text() to properly handle the SQL query
        from sqlalchemy import text
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)
    finally:
        engine.dispose()
    
    # Save to cache
    df.to_csv(cache_file, index=False)
    
    return df

def create_visualization(query_prompt: str):
    df = get_materials_data()
    
    # Handle predefined visualizations
    if query_prompt == "Create a line chart showing total material usage over time":
        #daily_usage = df.groupby('batch_date')['total_length_used'].sum().reset_index()
        daily_usage = df.groupby(pd.Grouper(key='batch_date', freq='W'))['total_length_used'].sum().reset_index()
        daily_usage['batch_date'] = daily_usage['batch_date'].dt.strftime('%d %b %Y')  # Format to 'DD MMM YYYY'

        fig = px.line(
            daily_usage,
            x='batch_date',
            y='total_length_used',
            title='Material Usage Over Time',
            labels={'batch_date': 'Date', 'total_length_used': 'Total Length Used (mm)'}
        )

        fig.update_xaxes(
            tickangle=-45,
            #dtick='M1', 
            nticks=12,    # Show 12 evenly spaced ticks
            showgrid=True
        )

        # Convert numpy types to native Python types
        return _make_json_serializable(fig)
    
    elif query_prompt == "Create a bar chart showing the top 10 materials by Total Length Used":
        top_materials = df.groupby('item_description')['total_length_used'].sum()\
            .sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_materials,
                     x='item_description',
                     y='total_length_used',
                     title='Top 10 Materials by Total Length Used',
                     labels={'item_description': 'Item Description',
                            'total_length_used': 'Total Length Used (mm)'})
        
        fig.update_xaxes(
            tickangle=-35,
        )

        return _make_json_serializable(fig)
    
    elif query_prompt == "Create a bar chart showing top 10 items by total offcut length":
        top_offcuts = df.groupby('item_description')['total_offcut_length_created'].sum()\
            .sort_values(ascending=True).head(10).reset_index()
        fig = px.bar(top_offcuts,
                     x='total_offcut_length_created',
                     y='item_description',
                     orientation='h',
                     title='Top 10 Items by Total Offcut Length Created',
                     labels={'item_description': 'Item Description',
                            'total_offcut_length_created': 'Total Offcut Length (mm)'})
        
        fig.update_yaxes(
            tickangle=-5,
        )

        return _make_json_serializable(fig)
    
    elif query_prompt == "Create a visualization of top and bottom 5 materials by efficiency":
        # Group by item_description and calculate mean efficiency
        avg_efficiency = df.groupby('item_description')['usage_efficiency'].mean()
        
        # Get top and bottom 5
        top_5 = avg_efficiency.nlargest(5)
        bottom_5 = avg_efficiency.nsmallest(5).sort_values(ascending=False)

        # Combine and reset index
        efficiency_data = pd.concat([top_5, bottom_5]).reset_index()
        
        # Create color list (5 green, 5 red)
        #colors = ['lightgreen']*5 + ['lightcoral']*5
        colors = ['green']*5 + ['red']*5
        
        # Create horizontal bar chart
        fig = px.bar(efficiency_data,
                    x='usage_efficiency',
                    y='item_description',
                    orientation='h',
                    title='Top and Bottom 5 Materials by Usage Efficiency',
                    labels={'item_description': 'Item Description',
                           'usage_efficiency': 'Usage Efficiency (%)'})
        
        # Update the colors and reverse the y-axis
        fig.update_traces(marker_color=colors)
        fig.update_layout(yaxis={'autorange': 'reversed'})
        fig.update_yaxes(
            tickangle=-5,
        )
        
        return _make_json_serializable(fig)
    
    # Handle custom queries using PandasAI
    else:
        smart_df = SmartDataframe(df, config={'llm': llm})
        enhanced_prompt = f"""
        Create a Plotly visualization for: {query_prompt}
        Use Plotly Express (px) to create the visualization.
        Return ONLY the Plotly figure object.
        Do not show the plot, just return the figure object.
        Make sure to include a descriptive title and proper axis labels.
        """
        
        try:
            result = smart_df.chat(enhanced_prompt)
            if hasattr(result, 'update_layout'):  # Check if it's a Plotly figure
                return _make_json_serializable(result)
            else:
                raise ValueError("Generated result is not a Plotly figure")
        except Exception as e:
            print(f"Error in create_visualization: {str(e)}")
            raise Exception("Failed to generate custom visualization. Please try a different query.")

def _make_json_serializable(fig):
    """Convert a Plotly figure to JSON-serializable format"""
    # First convert the figure to a dict
    fig_dict = fig.to_dict()
    
    # Function to convert numpy types to native Python types
    def convert_numpy(obj):
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_numpy(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(item) for item in obj]
        return obj
    
    # Convert all numpy types in the figure dict
    return convert_numpy(fig_dict)

