from flask import Blueprint, request, jsonify, session, Response
from werkzeug.utils import secure_filename
import os
from backend.app import db
from backend.models import Batch, BatchDetail, Item, Offcut, OffcutUsageHistory
from backend.data_pipeline import (
    preprocess_pdf, 
    ingest_data, 
    store_dataframe_temp, 
    retrieve_dataframe_temp
)
from datetime import datetime
import shutil
from tempfile import NamedTemporaryFile
from flask_sse import sse
import time

admin_bp = Blueprint('admin_bp', __name__)

UPLOAD_FOLDER = 'uploads/pdfs'
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure upload directory exists with proper permissions
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Ensure directory has read/write permissions
    os.chmod(UPLOAD_FOLDER, 0o755)
except Exception as e:
    print(f"Error setting up upload directory: {str(e)}")

def allowed_file(filename):
    """Validate file extension for PDF uploads"""
    if '.' not in filename:
        return False
        
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_batch_codes(df):
    """
    Validate that batch codes in the DataFrame don't already exist in the database
    Returns: (bool, list of existing batch codes)
    """
    batch_codes = df['Batch No'].unique()
    existing_batches = Batch.query.filter(Batch.batch_code.in_(batch_codes)).all()
    
    if existing_batches:
        existing_codes = [batch.batch_code for batch in existing_batches]
        return False, existing_codes
    return True, []

@admin_bp.route('/upload', methods=['POST'])
def upload_files():
    """Handle single PDF file upload for preprocessing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename
        }), 200
    
    return jsonify({'error': 'Invalid file format'}), 400

@admin_bp.route('/process', methods=['POST'])
def process_files():
    """Preprocess single uploaded PDF file"""
    try:
        print("Starting process_files endpoint")
        
        data = request.get_json()
        if not data:
            print("No JSON data received")
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        print("Received data:", data)
        
        batch_date = data.get('batch_date')
        filename = data.get('filename')
        
        if not batch_date or not filename:
            print(f"Missing required fields: batch_date={batch_date}, filename={filename}")
            return jsonify({'error': 'batch_date and filename are required'}), 400
            
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            print(f"File not found at path: {file_path}")
            return jsonify({'error': 'File not found'}), 404
            
        try:
            print(f"Processing PDF file: {file_path}")
            result = preprocess_pdf(file_path, batch_date)
            
            # Check if result is an error dictionary
            if isinstance(result, dict) and 'error' in result:
                if result['error'] == 'duplicate_batch':
                    return jsonify({
                        'error': 'duplicate_batch',
                        'batch_code': result['batch_code'],
                        'message': result['message']
                    }), 409
                    
            processed_df = result  # If no error, result is the DataFrame
            
            if processed_df is None or processed_df.empty:
                print("No data extracted from PDF")
                return jsonify({'error': 'No data could be extracted from PDF'}), 400
            
            print("PDF processed successfully, storing DataFrame")
            # Store DataFrame in temporary file
            temp_file_path = store_dataframe_temp(processed_df)
            session['temp_file_path'] = temp_file_path
            session['has_processed_data'] = True
            
            # Create preview data once and use it in the response
            preview_data = processed_df.head(20).to_dict('records')
            
            print("Returning successful response")
            return jsonify({
                'message': 'File processed successfully',
                'preview': preview_data
            }), 200
                
        finally:
            if os.path.exists(file_path):
                print(f"Cleaning up file: {file_path}")
                os.remove(file_path)
                
    except Exception as e:
        print(f"Error in process_files: {str(e)}")
        import traceback
        print("Traceback:", traceback.format_exc())
        return jsonify({
            'error': 'Processing failed',
            'details': str(e)
        }), 500

@admin_bp.route('/ingest', methods=['POST'])
def ingest_processed_data():
    """Ingest preprocessed data into database"""
    try:
        print("Starting ingest_processed_data endpoint")
        
        if not session.get('has_processed_data', False):
            print("No processed data flag in session")
            return jsonify({'error': 'No processed data found'}), 400
            
        temp_file_path = session.get('temp_file_path')
        if not temp_file_path or not os.path.exists(temp_file_path):
            print(f"Temp file not found: {temp_file_path}")
            return jsonify({'error': 'Processed data not found'}), 400
            
        try:
            processed_df = retrieve_dataframe_temp(temp_file_path)
            print(f"Retrieved DataFrame with {len(processed_df)} rows")
            
            # Start transaction here
            db.session.begin()
            
            try:
                result = ingest_data(processed_df)
                db.session.commit()
                
                # Clear session
                session.pop('temp_file_path', None)
                session.pop('has_processed_data', None)
                
                return jsonify({
                    'message': 'Data ingested successfully',
                    'summary': result
                }), 200
                
            except Exception as e:
                db.session.rollback()
                raise e
                
        except Exception as e:
            print(f"Error processing DataFrame: {str(e)}")
            import traceback
            print("Traceback:", traceback.format_exc())
            raise
            
    except Exception as e:
        print(f"Error in ingest_processed_data: {str(e)}")
        import traceback
        print("Traceback:", traceback.format_exc())
        return jsonify({
            'error': 'Failed to ingest data',
            'details': str(e)
        }), 500

@admin_bp.route('/status', methods=['GET'])
def get_ingestion_status():
    """Get current database statistics"""
    try:
        stats = {
            'total_batches': Batch.query.count(),
            'total_items': Item.query.count(),
            'total_offcuts': Offcut.query.count(),
            'total_available_offcuts': Offcut.query.filter_by(is_available=True).count(),
            'recent_batches': [
                {
                    'batch_code': b.batch_code,
                    'batch_date': b.batch_date.strftime('%Y-%m-%d')
                }
                for b in Batch.query.order_by(Batch.batch_code.desc()).limit(5)
            ]
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/process-status')
def process_status():
    def generate():
        stages = [
            ("Parsing PDF", 20),
            ("Extracting Data", 40),
            ("Validating Content", 60),
            ("Preparing Database Records", 80),
            ("Completing Process", 100)
        ]
        
        for stage, progress in stages:
            yield f'data: {{"status": "{stage}", "progress": {progress}}}\n\n'
            time.sleep(1)  # Simulate processing time
            
    return Response(generate(), mimetype='text/event-stream')

@admin_bp.route('/available-offcuts', methods=['GET'])
def get_available_offcuts():
    """Retrieve all available offcuts."""
    try:
        offcuts = Offcut.query.filter_by(is_available=True)\
            .order_by(Offcut.created_in_batch_detail_id.desc())\
            .all()
        
        return jsonify([{
            'offcut_id': o.offcut_id,
            'legacy_offcut_id': o.legacy_offcut_id,
            'length_mm': o.length_mm,
            'material_profile': o.material_profile,
            'created_in_batch_detail_id': o.created_in_batch_detail_id,
            'reuse_count': o.reuse_count
        } for o in offcuts]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/update-offcut-usage', methods=['POST'])
def update_offcut_usage():
    """Update offcut usage history and status."""
    data = request.get_json()
    offcut_ids = data.get('offcut_ids', [])
    batch_code = data.get('batch_code')
    reuse_date = data.get('reuse_date')

    if not offcut_ids or not batch_code or not reuse_date:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Validate batch exists
        batch = Batch.query.filter_by(batch_code=batch_code).first()
        if not batch:
            return jsonify({'error': 'Invalid batch code'}), 404

        # Update each offcut
        for offcut_id in offcut_ids:
            offcut = Offcut.query.get(offcut_id)
            if offcut:
                # Create usage history entry
                usage_history = OffcutUsageHistory(
                    offcut_id=offcut_id,
                    batch_id=batch.batch_id,
                    reuse_success=True,
                    reuse_date=datetime.strptime(reuse_date, '%Y-%m-%d').date()
                )
                db.session.add(usage_history)

                # Update offcut status
                offcut.is_available = False
                offcut.reuse_count += 1

        db.session.commit()
        return jsonify({'message': 'Usage history updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500