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
import logging
import gc

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
    try:
        # Load data in smaller chunks
        df = get_materials_data()
        
        if query_prompt == "Create a line chart showing total material usage over time":
            # Process data in chunks to reduce memory usage
            df['batch_date'] = pd.to_datetime(df['batch_date'])
            
            # Aggregate data immediately to reduce memory footprint
            agg_data = (df.groupby('batch_date')['total_length_used']
                       .sum()
                       .resample('W')
                       .sum()
                       .reset_index())
            
            # Convert dates after aggregation
            agg_data['batch_date'] = agg_data['batch_date'].dt.strftime('%d %b %Y')
            
            # Clear original dataframe from memory
            del df
            gc.collect()
            
            fig = px.line(agg_data, x='batch_date', y='total_length_used',
                         title='Material Usage Over Time',
                         labels={'batch_date': 'Date', 
                                'total_length_used': 'Total Length Used (mm)'})
            
            fig.update_xaxes(tickangle=-45, nticks=12)
            del agg_data
            return _make_json_serializable(fig)
        
        elif query_prompt == "Create a bar chart showing the top 10 materials by Total Length Used":
            # Aggregate immediately to reduce memory
            top_materials = (df.groupby('item_description')['total_length_used']
                           .sum()
                           .sort_values(ascending=False)
                           .head(10)
                           .reset_index())
            
            del df
            gc.collect()
            
            fig = px.bar(top_materials,
                        x='item_description',
                        y='total_length_used',
                        title='Top 10 Materials by Total Length Used',
                        labels={'item_description': 'Item Description',
                               'total_length_used': 'Total Length Used (mm)'})
            
            fig.update_xaxes(tickangle=-35)
            del top_materials
            return _make_json_serializable(fig)
        
        elif query_prompt == "Create a bar chart showing top 10 items by total offcut length":
            # Aggregate immediately to reduce memory
            top_offcuts = (df.groupby('item_description')['total_offcut_length_created']
                          .sum()
                          .sort_values(ascending=True)
                          .head(10)
                          .reset_index())
            
            del df
            gc.collect()
            
            fig = px.bar(top_offcuts,
                        x='total_offcut_length_created',
                        y='item_description',
                        orientation='h',
                        title='Top 10 Items by Total Offcut Length Created',
                        labels={'item_description': 'Item Description',
                               'total_offcut_length_created': 'Total Offcut Length (mm)'})
            
            fig.update_yaxes(tickangle=-5)
            del top_offcuts
            return _make_json_serializable(fig)
        
        elif query_prompt == "Create a visualization of top and bottom 5 materials by efficiency":
            # Aggregate immediately to reduce memory
            avg_efficiency = df.groupby('item_description')['usage_efficiency'].mean()
            del df
            gc.collect()
            
            # Get top and bottom 5
            top_5 = avg_efficiency.nlargest(5)
            bottom_5 = avg_efficiency.nsmallest(5)
            del avg_efficiency
            
            # Combine and reset index
            efficiency_data = pd.concat([top_5, bottom_5]).reset_index()
            del top_5, bottom_5
            gc.collect()
            
            colors = ['green']*5 + ['red']*5
            
            fig = px.bar(efficiency_data,
                        x='usage_efficiency',
                        y='item_description',
                        orientation='h',
                        title='Top and Bottom 5 Materials by Usage Efficiency',
                        labels={'item_description': 'Item Description',
                               'usage_efficiency': 'Usage Efficiency (%)'})
            
            fig.update_traces(marker_color=colors)
            fig.update_layout(yaxis={'autorange': 'reversed'})
            fig.update_yaxes(tickangle=-5)
            
            del efficiency_data
            return _make_json_serializable(fig)
        
        # Custom queries are disabled to prevent memory issues
        else:
            raise Exception("Custom visualizations are temporarily disabled to conserve memory")
            
    except Exception as e:
        logging.error(f"Visualization error: {str(e)}")
        raise Exception("Failed to generate visualization due to memory constraints")

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

