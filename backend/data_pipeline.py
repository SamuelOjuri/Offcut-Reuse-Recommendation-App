import os
import pandas as pd
import re
from llama_parse import LlamaParse
from datetime import datetime
from backend.app import db
from backend.models import Batch, BatchDetail, Item, Offcut, BatchItem, BatchOffcutSuggestion, OffcutUsageHistory
from tempfile import NamedTemporaryFile

def preprocess_pdf(file_path, batch_date=None):
    """Preprocess single PDF file using LlamaParse"""
    if batch_date is None:
        raise ValueError("batch_date must be provided for preprocessing")
        
    parser_text = LlamaParse(result_type="text")
    all_data = []
    
    try:
        if not os.path.isfile(file_path):
            raise ValueError(f"File not found: {file_path}")
            
        docs_text = parser_text.load_data(file_path)
        if not docs_text:
            raise ValueError(f"No text content extracted from {file_path}")
        text_data = "\n\n".join([doc.get_content() for doc in docs_text])
        
        # Parse the text data
        parsed_data = parse_data(text_data)
        
        # Early batch code validation
        batch_code = parsed_data[0].get('Batch No') if parsed_data else None
        if not batch_code:
            raise ValueError(f"No batch code found in {os.path.basename(file_path)}")
            
        # Check if batch exists - return specific error type
        if Batch.query.filter_by(batch_code=batch_code).first():
            return {
                'error': 'duplicate_batch',
                'batch_code': batch_code,
                'message': f"Batch code {batch_code} already exists in database"
            }
        
        # Convert to DataFrame
        df = create_dataframe(parsed_data)
        df['source_file'] = os.path.basename(file_path)
        df['batch_date'] = batch_date
        all_data.append(df)
        
    except Exception as e:
        raise Exception(f"Failed to process PDF {file_path}: {str(e)}")

    if not all_data:
        raise Exception("No valid data found for processing")
        
    return pd.concat(all_data, ignore_index=True)

def parse_data(text_data):
    data = []
    batch_no = None
    saw_name = None

    sections = re.split(r'\s*BAR OPTIMISING\s*', text_data)

    for section in sections:
        if "BATCH:" in section:
            batch_no_match = re.search(r'BATCH:\s*(\S+)', section)
            if batch_no_match:
                batch_no = batch_no_match.group(1).strip()

        if "Saw:" in section:
            saw_name_match = re.search(r'Saw:\s*(.+)', section)
            if saw_name_match:
                saw_name = saw_name_match.group(1).strip()

        products = re.findall(r'(Product Code:\s*\S+[\s\S]*?)(?=Product Code:|$)', section)
        for product in products:
            item = {
                'Batch No': batch_no,
                'Saw Name': saw_name,
            }

            # Extract data using optimized regex patterns
            patterns = {
                'Product Code': r'Product Code:\s*(\S+)',
                'Product Description': r'Description:\s*(.+)',
                'Input Bar Length': r'Bar Length:\s*(\d+)',
                'Suggested Offcut ID(s)': r'Use Offcut[s]?:\s*([\d\s&]*)',
                'Bar Length Used': r'Total Used:\s*(\d+)',
                'Offcut ID(s) Created': r'Save Offcut[s]?:\s*([\d\s&]*)'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, product)
                if match:
                    value = match.group(1).strip()
                    if key in ['Input Bar Length', 'Bar Length Used']:
                        value = int(value)
                    item[key] = value
                else:
                    item[key] = 'None' if 'ID' in key else 0

            item['Double Cut'] = 'Yes' if "*** Double Cut Bars ***" in product else 'No'
            data.append(item)

    return data

def create_dataframe(parsed_data):
    """Convert parsed data to DataFrame"""
    rows = []
    for item in parsed_data:
        quantity = 2 if item['Double Cut'] == 'Yes' else 1
        total_length_used = quantity * item['Bar Length Used']
        offcut_length_created = item['Input Bar Length'] - item['Bar Length Used']
        total_input_length = item['Input Bar Length'] * quantity
        total_offcut_length_created = quantity * offcut_length_created

        row = {
            'Batch No': item['Batch No'],
            'Saw Name': item['Saw Name'],
            'Item Code': item['Product Code'],
            'Item Description': item['Product Description'],
            'Input Bar Length': item['Input Bar Length'],
            'Total Input Length': total_input_length,
            'Suggested Offcut ID(s)': item['Suggested Offcut ID(s)'],
            'Double Cut': item['Double Cut'],
            'Quantity': quantity,
            'Bar Length Used': item['Bar Length Used'],
            'Total Length Used': total_length_used,
            'Offcut Length Created': offcut_length_created,
            'Total Offcut Length Created': total_offcut_length_created,
            'Offcut ID(s) Created': item['Offcut ID(s) Created'],
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df['Waste Percentage'] = (df['Total Offcut Length Created'] / df['Input Bar Length']) * 100
    df['Usage Efficiency'] = (df['Total Length Used'] / df['Input Bar Length']) * 100
  
    return df

def validate_input_data(df):
    """Validate required columns are present in DataFrame"""
    expected_columns = [
        'Batch No', 'batch_date', 'Saw Name', 'Item Code', 
        'Item Description', 'Quantity', 'Input Bar Length',
        'Total Input Length', 'Bar Length Used',
        'Total Length Used', 'Offcut Length Created'
    ]
    
    if not all(col in df.columns for col in expected_columns):
        missing_columns = [col for col in expected_columns if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    return True

def validate_dataframe_for_ingestion(df):
    """Additional validation before ingestion"""
    try:
        # Check for required columns
        required_columns = [
            'Batch No', 'batch_date', 'Saw Name', 'Item Code', 
            'Item Description', 'Quantity', 'Input Bar Length',
            'Bar Length Used', 'Total Length Used', 'Offcut Length Created',
            'Double Cut', 'Waste Percentage', 'Usage Efficiency'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        # Check for null values in critical columns
        critical_columns = ['Batch No', 'Item Code', 'Item Description']
        null_columns = [col for col in critical_columns if df[col].isnull().any()]
        if null_columns:
            raise ValueError(f"Null values found in critical columns: {null_columns}")
            
        # Validate numeric columns
        numeric_columns = ['Quantity', 'Input Bar Length', 'Bar Length Used']
        for col in numeric_columns:
            if not pd.to_numeric(df[col], errors='coerce').notnull().all():
                raise ValueError(f"Invalid numeric values in column: {col}")
                
        return True
        
    except Exception as e:
        raise ValueError(f"DataFrame validation failed: {str(e)}")

def ingest_data(df):
    """Ingest DataFrame directly into database"""
    try:
        print("Starting data ingestion...")
        # Validate input data
        validate_input_data(df)
        validate_dataframe_for_ingestion(df)
        print("Input data validated")
        
        # Filter out Steel Saw records before processing
        df = df[df['Saw Name'] != 'Steel Saw'].copy()
        print(f"Processing {len(df)} records after filtering")
        
        batch_ids = {}
        item_ids = {}
        batch_detail_ids = {}
        
        # Process each batch
        for batch_code, batch_group in df.groupby('Batch No'):
            print(f"Processing batch: {batch_code}")
            try:
                batch_date = pd.to_datetime(batch_group['batch_date'].iloc[0]).date()
            except Exception as e:
                raise ValueError(f"Invalid batch date for batch {batch_code}: {str(e)}")
            
            # Create or get existing batch
            batch = Batch.query.filter_by(batch_code=batch_code).first()
            if not batch:
                batch = Batch(batch_code=batch_code, batch_date=batch_date)
                db.session.add(batch)
                db.session.flush()
            batch_ids[batch_code] = batch.batch_id
            
            try:
                batch_detail = BatchDetail(
                    batch_id=batch.batch_id,
                    saw_name=batch_group['Saw Name'].iloc[0],
                    source_file=batch_group['source_file'].iloc[0]
                )
                db.session.add(batch_detail)
                db.session.flush()
                batch_detail_ids[batch_code] = batch_detail.batch_detail_id
                
                # Process items and batch items
                for idx, item_row in batch_group.iterrows():
                    try:
                        # Process item
                        item = Item.query.filter_by(item_description=item_row['Item Description']).first()
                        if not item:
                            item = Item(
                                item_code=item_row['Item Code'],
                                item_description=item_row['Item Description']
                            )
                            db.session.add(item)
                            db.session.flush()
                        item_ids[item_row['Item Description']] = item.item_id
                        
                        # Create batch item
                        batch_item = BatchItem(
                            batch_id=batch.batch_id,
                            item_id=item.item_id,
                            quantity=item_row['Quantity'],
                            input_bar_length_mm=item_row['Input Bar Length'],
                            bar_length_used_mm=item_row['Bar Length Used'],
                            total_length_used_mm=item_row['Total Length Used'],
                            offcut_length_created_mm=item_row['Offcut Length Created'],
                            total_offcut_length_created_mm=item_row['Total Offcut Length Created'],
                            double_cut=item_row['Double Cut'] == 'Yes',
                            waste_percentage=item_row['Waste Percentage'],
                            usage_efficiency=item_row['Usage Efficiency']
                        )
                        db.session.add(batch_item)
                        
                        # Process offcuts and suggestions with error handling
                        if pd.notna(item_row['Offcut ID(s) Created']) and str(item_row['Offcut ID(s) Created']).lower() != 'none':
                            process_offcuts(item_row, batch_detail, db.session)
                        
                        if pd.notna(item_row['Suggested Offcut ID(s)']):
                            try:
                                process_suggestions(item_row, batch, batch_detail, db.session)
                            except Exception as e:
                                print(f"Warning: Failed to process suggestions for item {idx}: {str(e)}")
                                # Continue processing other items
                                continue
                                
                    except Exception as e:
                        raise ValueError(f"Failed to process item at index {idx}: {str(e)}")
                        
            except Exception as e:
                raise ValueError(f"Failed to process batch {batch_code}: {str(e)}")
                
        print("All batches processed successfully")
        return {"message": "Data ingestion completed successfully"}
        
    except Exception as e:
        print(f"Error during data ingestion: {str(e)}")
        raise Exception(f"Data ingestion failed: {str(e)}")

def store_dataframe_temp(df):
    """Store DataFrame in a temporary file"""
    with NamedTemporaryFile(prefix='processed_data_', suffix='.pkl', delete=False) as temp_file:
        df.to_pickle(temp_file.name)
        return temp_file.name

def retrieve_dataframe_temp(file_path):
    """Retrieve DataFrame from temporary file"""
    try:
        df = pd.read_pickle(file_path)
        os.unlink(file_path)  # Clean up the temporary file
        return df
    except Exception as e:
        if os.path.exists(file_path):
            os.unlink(file_path)
        raise Exception(f"Failed to retrieve DataFrame: {str(e)}")

def process_offcuts(item_row, batch_detail, session):
    """Helper function to process offcuts"""
    offcut_ids = str(item_row['Offcut ID(s) Created']).split('&')
    for i, offcut_id in enumerate(offcut_ids):
        related_id = int(offcut_ids[i-1].strip()) if item_row['Double Cut'] == 'Yes' and i > 0 else None
        
        offcut = Offcut(
            legacy_offcut_id=int(offcut_id.strip()),
            length_mm=item_row['Offcut Length Created'],
            material_profile=item_row['Item Description'],
            created_in_batch_detail_id=batch_detail.batch_detail_id,
            related_legacy_offcut_id=related_id,
            is_available=True,
            reuse_count=0
        )
        session.add(offcut)

def process_suggestions(item_row, batch, batch_detail, session):
    """Helper function to process suggestions"""
    # Skip if no valid suggestions
    if pd.isna(item_row['Suggested Offcut ID(s)']) or str(item_row['Suggested Offcut ID(s)']).lower() == 'none':
        return
        
    suggested_ids = str(item_row['Suggested Offcut ID(s)']).split('&')
    
    # Validate first ID
    try:
        primary_id = int(suggested_ids[0].strip())
    except (ValueError, TypeError):
        print(f"Invalid primary offcut ID: {suggested_ids[0]}")
        return
        
    # Validate second ID if it exists
    secondary_id = None
    if len(suggested_ids) > 1:
        try:
            secondary_id = int(suggested_ids[1].strip())
        except (ValueError, TypeError):
            print(f"Invalid secondary offcut ID: {suggested_ids[1]}")
            # Continue with only primary ID
    
    suggestion = BatchOffcutSuggestion(
        batch_id=batch.batch_id,
        offcut_legacy_id_1=primary_id,
        offcut_legacy_id_2=secondary_id,
        matched_profile=item_row['Item Description'],
        suggested_length_mm=item_row['Offcut Length Created'],
        batch_detail_id=batch_detail.batch_detail_id
    )
    session.add(suggestion)