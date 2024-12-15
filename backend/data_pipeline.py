import os
import pandas as pd
import re
from llama_parse import LlamaParse
from datetime import datetime
from backend.app import db
from backend.models import Batch, BatchDetail, Item, Offcut, BatchItem, BatchOffcutSuggestion, OffcutUsageHistory

def preprocess_pdf(data_folder, batch_date=None):
    """Preprocess PDF files using LlamaParse"""
    if batch_date is None:
        raise ValueError("batch_date must be provided for preprocessing")
        
    parser_text = LlamaParse(result_type="text")
    all_data = []

    for filename in os.listdir(data_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(data_folder, filename)
            
            # Extract text from PDF
            docs_text = parser_text.load_data(pdf_path)
            text_data = "\n\n".join([doc.get_content() for doc in docs_text])
            
            # Parse the text data
            parsed_data = parse_data(text_data)
            
            # Convert to DataFrame
            df = create_dataframe(parsed_data)
            df['source_file'] = filename
            df['batch_date'] = batch_date  # Add batch_date to DataFrame
            all_data.append(df)

    # Combine all DataFrames
    if not all_data:
        raise Exception("No valid PDF files found for processing")
        
    return pd.concat(all_data, ignore_index=True)

def parse_data(text_data):
    data = []
    batch_no = None
    saw_name = None

    # Split the text into sections by detecting each "BAR OPTIMISING" header
    sections = re.split(r'\s*BAR OPTIMISING\s*', text_data)

    for section in sections:
        # Update Batch No and Saw Name if found in the current section
        if "BATCH:" in section:
            batch_no_match = re.search(r'BATCH:\s*(\S+)', section)
            if batch_no_match:
                batch_no = batch_no_match.group(1).strip()

        if "Saw:" in section:
            saw_name_match = re.search(r'Saw:\s*(.+)', section)
            if saw_name_match:
                saw_name = saw_name_match.group(1).strip()

        # Process sections with product information
        products = re.findall(r'(Product Code:\s*\S+[\s\S]*?)(?=Product Code:|$)', section)
        for product in products:
            item = {
                'Batch No': batch_no,
                'Saw Name': saw_name,
            }

            # Extract Product Code (updated regex to capture alphanumeric codes)
            product_code_match = re.search(r'Product Code:\s*(\S+)', product)
            if product_code_match:
                item['Product Code'] = product_code_match.group(1).strip()

            # Extract Description
            description_match = re.search(r'Description:\s*(.+)', product)
            if description_match:
                item['Product Description'] = description_match.group(1).strip()

            # Extract Bar Length
            bar_length_match = re.search(r'Bar Length:\s*(\d+)', product)
            if bar_length_match:
                item['Input Bar Length'] = int(bar_length_match.group(1).strip())

            # Extract Suggested Offcut IDs
            offcut_match = re.search(r'Use Offcut[s]?:\s*([\d\s&]*)', product)
            item['Suggested Offcut ID(s)'] = offcut_match.group(1).strip() if offcut_match else 'None'

            # Determine if Double Cut
            item['Double Cut'] = 'Yes' if "*** Double Cut Bars ***" in product else 'No'

            # Calculate Total Length Used and Offcut
            total_used_match = re.search(r'Total Used:\s*(\d+)', product)
            #offcut_length_match = re.search(r'Offcut:\s*(\d+)', product)

            item['Bar Length Used'] = int(total_used_match.group(1).strip()) if total_used_match else 0
            #item['Offcut Length Created'] = int(offcut_length_match.group(1).strip()) if offcut_length_match else 0

            # Extract Offcut ID(s) Created
            save_offcut_match = re.search(r'Save Offcut[s]?:\s*([\d\s&]*)', product)
            item['Offcut ID(s) Created'] = save_offcut_match.group(1).strip() if save_offcut_match else 'None'

            # Add the extracted data to the list
            data.append(item)

    return data

def create_dataframe(parsed_data):
    """Convert parsed data to DataFrame"""
    rows = []
    for item in parsed_data:
        # Determine Quantity based on Double Cut
        quantity = 2 if item['Double Cut'] == 'Yes' else 1

        # Calculate Total Length Used
        total_length_used = quantity * item['Bar Length Used']

        # Calculate Offcut Length Created
        offcut_length_created = item['Input Bar Length'] - item['Bar Length Used']

        # Calculate Total Input Length
        total_input_length = item['Input Bar Length'] * quantity

        # Calculate Total Offcut Length Created
        total_offcut_length_created = quantity * offcut_length_created

        # Create the row with all columns including the derived ones
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

    # Calculate Waste Percentage
    df['Waste Percentage'] = (df['Total Offcut Length Created'] / df['Input Bar Length']) * 100

    # Calculate Usage Efficiency
    df['Usage Efficiency'] = (df['Total Length Used'] / df['Input Bar Length']) * 100
  
    return df 

def ingest_data(df):
    """Ingest DataFrame directly into database"""
    try:
        # Filter out Steel Saw records before processing
        df = df[df['Saw Name'] != 'Steel Saw'].copy()
        
        # Begin database transaction
        with db.session.begin():
            batch_ids = {}  # Track batch IDs
            item_ids = {}   # Track item IDs
            batch_detail_ids = {}  # Track batch detail IDs
            
            # Process each batch
            for batch_code, batch_group in df.groupby('Batch No'):
                batch_date = pd.to_datetime(batch_group['batch_date'].iloc[0]).date()
                
                # 1. Create batch record
                batch = Batch(
                    batch_code=batch_code,
                    batch_date=batch_date
                )
                db.session.add(batch)
                db.session.flush()
                batch_ids[batch_code] = batch.batch_id
                
                # 2. Insert batch details
                batch_detail = BatchDetail(
                    batch_id=batch.batch_id,
                    saw_name=batch_group['Saw Name'].iloc[0],
                    source_file=batch_group['source_file'].iloc[0]
                )
                db.session.add(batch_detail)
                db.session.flush()
                batch_detail_ids[batch_code] = batch_detail.batch_detail_id
                
                # 3. Process items and batch items
                for _, item_row in batch_group.iterrows():
                    # Check if item exists or create new
                    item = Item.query.filter_by(item_description=item_row['Item Description']).first()
                    if not item:
                        item = Item(
                            item_code=item_row['Item Code'],
                            item_description=item_row['Item Description']
                        )
                        db.session.add(item)
                        db.session.flush()
                    item_ids[item_row['Item Description']] = item.item_id
                    
                    # 4. Create batch item
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
                    
                    # 5. Handle offcuts
                    if pd.notna(item_row['Offcut ID(s) Created']) and item_row['Offcut ID(s) Created'] != 'None':
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
                            db.session.add(offcut)
                    
                    # 6. Handle batch offcut suggestions
                    if pd.notna(item_row['Suggested Offcut ID(s)']):
                        suggested_ids = str(item_row['Suggested Offcut ID(s)']).split('&')
                        primary_id = int(suggested_ids[0].strip())
                        secondary_id = int(suggested_ids[1].strip()) if len(suggested_ids) > 1 else None
                        
                        suggestion = BatchOffcutSuggestion(
                            batch_id=batch.batch_id,
                            offcut_legacy_id_1=primary_id,
                            offcut_legacy_id_2=secondary_id,
                            matched_profile=item_row['Item Description'],
                            suggested_length_mm=item_row['Offcut Length Created'],
                            batch_detail_id=batch_detail.batch_detail_id
                        )
                        db.session.add(suggestion)
                        
                        # 7. Create offcut usage history
                        for legacy_offcut_id in suggested_ids:
                            offcut = Offcut.query.filter_by(legacy_offcut_id=int(legacy_offcut_id.strip())).first()
                            if offcut:
                                usage_history = OffcutUsageHistory(
                                    offcut_id=offcut.offcut_id,
                                    batch_id=batch.batch_id,
                                    reuse_success=True,
                                    reuse_date=batch_date
                                )
                                db.session.add(usage_history)
                                
                                # Update offcut availability and reuse count
                                offcut.is_available = False
                                offcut.reuse_count += 1

        return {"message": "Data ingestion completed successfully"}
        
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Data ingestion failed: {str(e)}")
