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
from sqlalchemy import text

# from dotenv import load_dotenv
# load_dotenv()

# openai_api_key = os.getenv("OPENAI_API_KEY")

# llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)  # Example: Replace 'gpt-4' with your desired model


def get_materials_data(force_refresh=False, chunk_size=1000):
    """Get materials data with chunking support"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # Test query first
            test_query = "SELECT COUNT(*) FROM batch_items"
            result = connection.execute(text(test_query)).scalar()
            print(f"Number of records in batch_items: {result}")
            
            if result == 0:
                raise Exception("No records found in batch_items table")
            
            # Query with proper JOINs
            query = text("""
                SELECT b.batch_date, i.item_description, 
                       bi.total_length_used_mm as total_length_used,
                       bi.total_offcut_length_created_mm as total_offcut_length_created,
                       bi.usage_efficiency
                FROM batch_items bi
                JOIN batches b ON bi.batch_id = b.batch_id
                JOIN items i ON bi.item_id = i.item_id
                ORDER BY b.batch_date
            """)
            
            # Execute query with chunking
            result = connection.execution_options(stream_results=True).execute(query)
            while True:
                chunk = result.fetchmany(chunk_size)
                if not chunk:
                    break
                df_chunk = pd.DataFrame(chunk)
                if not df_chunk.empty:
                    yield df_chunk
                    
    except Exception as e:
        logging.error(f"Database error in get_materials_data: {str(e)}")
        raise
    finally:
        engine.dispose()

def create_visualization(query_prompt: str):
    try:
        chunks = list(get_materials_data())
        
        if not chunks:
            raise Exception("No data available in the database")
            
        if query_prompt == "Create a line chart showing total material usage over time":
            all_data = []
            
            for chunk in chunks:
                if chunk.empty:
                    continue
                    
                try:
                    # Convert batch_date to datetime and format as string immediately
                    chunk['batch_date'] = pd.to_datetime(chunk['batch_date']).dt.strftime('%Y-%m-%d')
                    chunk_data = (chunk.groupby('batch_date')['total_length_used']
                                .sum()
                                .reset_index())
                    all_data.append(chunk_data)
                except Exception as e:
                    logging.error(f"Error processing chunk: {str(e)}")
                    continue
            
            if not all_data:
                raise Exception("No valid data available for visualization")
                
            agg_data = pd.concat(all_data, ignore_index=True)
            agg_data = (agg_data.groupby('batch_date')['total_length_used']
                       .sum()
                       .reset_index())
            
            # Sort by date string
            agg_data = agg_data.sort_values('batch_date')
            
            fig = px.line(
                agg_data,
                x='batch_date',
                y='total_length_used',
                title='Material Usage Over Time',
                labels={
                    'batch_date': 'Date',
                    'total_length_used': 'Total Length Used (mm)'
                }
            )
            
            fig.update_xaxes(tickangle=-45, dtick='M1', nticks=12)
            
            del agg_data
            gc.collect()
            
            return _make_json_serializable(fig)
        
        elif query_prompt == "Create a bar chart showing the top 10 materials by Total Length Used":
            # Process chunks individually and maintain running totals
            material_totals = {}
            
            for chunk in chunks:
                # Process each chunk
                chunk_totals = chunk.groupby('item_description')['total_length_used'].sum()
                
                # Update running totals
                for material, total in chunk_totals.items():
                    material_totals[material] = material_totals.get(material, 0) + total
            
            # Convert to DataFrame and get top 10
            top_materials = (pd.Series(material_totals)
                           .sort_values(ascending=False)
                           .head(10)
                           .reset_index())
            top_materials.columns = ['item_description', 'total_length_used']
            
            fig = px.bar(top_materials,
                        x='item_description',
                        y='total_length_used',
                        title='Top 10 Materials by Total Length Used',
                        labels={'item_description': 'Item Description',
                               'total_length_used': 'Total Length Used (mm)'})
            
            fig.update_xaxes(tickangle=-35)
            return _make_json_serializable(fig)
        
        elif query_prompt == "Create a bar chart showing top 10 items by total offcut length":
            # Process chunks individually and maintain running totals
            offcut_totals = {}
            
            for chunk in chunks:
                # Process each chunk
                chunk_totals = chunk.groupby('item_description')['total_offcut_length_created'].sum()
                
                # Update running totals
                for item, total in chunk_totals.items():
                    offcut_totals[item] = offcut_totals.get(item, 0) + total
            
            # Convert to DataFrame and get top 10
            top_offcuts = (pd.Series(offcut_totals)
                          .sort_values(ascending=True)
                          .head(10)
                          .reset_index())
            top_offcuts.columns = ['item_description', 'total_offcut_length_created']
            
            fig = px.bar(top_offcuts,
                        x='total_offcut_length_created',
                        y='item_description',
                        orientation='h',
                        title='Top 10 Items by Total Offcut Length Created',
                        labels={'item_description': 'Item Description',
                               'total_offcut_length_created': 'Total Offcut Length (mm)'})
            
            fig.update_yaxes(tickangle=-5)
            return _make_json_serializable(fig)
        
        elif query_prompt == "Create a visualization of top and bottom 5 materials by efficiency":
            # Process chunks individually and maintain running averages
            efficiency_totals = {}
            efficiency_counts = {}
            
            for chunk in chunks:
                # Process each chunk
                chunk_groups = chunk.groupby('item_description')
                
                # Update running totals and counts for calculating mean
                for name, group in chunk_groups:
                    # Convert usage_efficiency to numeric, handling any non-numeric values
                    eff_values = pd.to_numeric(group['usage_efficiency'], errors='coerce')
                    eff_sum = eff_values.sum()
                    eff_count = eff_values.count()  # Only counts non-null values
                    
                    if eff_count > 0:  # Only update if we have valid values
                        efficiency_totals[name] = efficiency_totals.get(name, 0) + eff_sum
                        efficiency_counts[name] = efficiency_counts.get(name, 0) + eff_count
            
            # Calculate averages and ensure numeric type
            avg_efficiency = {
                name: float(efficiency_totals[name] / efficiency_counts[name])
                for name in efficiency_totals.keys()
                if efficiency_counts[name] > 0
            }
            
            # Convert to Series with explicit numeric dtype
            avg_efficiency = pd.Series(avg_efficiency, dtype=float)
            
            # Get top and bottom 5
            top_5 = avg_efficiency.nlargest(5)
            bottom_5 = avg_efficiency.nsmallest(5)
            
            # Combine and reset index
            efficiency_data = pd.concat([top_5, bottom_5]).reset_index()
            efficiency_data.columns = ['item_description', 'usage_efficiency']
            
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
            
            return _make_json_serializable(fig)
        
        else:
            raise Exception("Invalid visualization type selected")
            
    except Exception as e:
        logging.error(f"Visualization error: {str(e)}")
        raise

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

