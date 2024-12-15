from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from backend.app import db
from backend.models import Batch, BatchDetail, Item, Offcut
from backend.data_pipeline import preprocess_pdf, ingest_data
from datetime import datetime
import pandas as pd

admin_bp = Blueprint('admin_bp', __name__)

UPLOAD_FOLDER = 'uploads/pdfs'
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        data = request.get_json()
        batch_date = data.get('batch_date')
        filename = data.get('filename')
        
        if not batch_date or not filename:
            return jsonify({'error': 'batch_date and filename are required'}), 400
            
        try:
            batch_date = datetime.strptime(batch_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        temp_dir = os.path.join(UPLOAD_FOLDER, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        import shutil
        shutil.copy2(file_path, os.path.join(temp_dir, filename))
        processed_df = preprocess_pdf(temp_dir, batch_date)
        
        # Validate batch codes before proceeding
        is_valid, existing_codes = validate_batch_codes(processed_df)
        if not is_valid:
            return jsonify({
                'error': 'Duplicate batch codes found',
                'existing_codes': existing_codes,
                'message': 'These batch codes already exist in the database'
            }), 409  # HTTP 409 Conflict
        
        # Store the DataFrame in the session
        from flask import session
        session['processed_df'] = processed_df.to_dict()
        
        shutil.rmtree(temp_dir)
        
        return jsonify({
            'message': 'File processed successfully',
            'preview': processed_df.head(5).to_dict('records'),
            'batch_date': batch_date.strftime('%Y-%m-%d'),
            'filename': filename,
            'batch_codes': processed_df['Batch No'].unique().tolist()  # Return batch codes for reference
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/ingest', methods=['POST'])
def ingest_processed_data():
    """Ingest preprocessed data into database"""
    try:
        from flask import session
        if 'processed_df' not in session:
            return jsonify({'error': 'No processed data found'}), 400
            
        processed_df = pd.DataFrame.from_dict(session['processed_df'])
        
        # Double-check validation before ingestion
        is_valid, existing_codes = validate_batch_codes(processed_df)
        if not is_valid:
            return jsonify({
                'error': 'Duplicate batch codes found',
                'existing_codes': existing_codes,
                'message': 'These batch codes already exist in the database'
            }), 409
        
        result = ingest_data(processed_df)
        
        # Clear the processed data from session
        session.pop('processed_df', None)
        
        return jsonify({
            'message': 'Data ingested successfully',
            'summary': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/status', methods=['GET'])
def get_ingestion_status():
    """Get current database statistics"""
    try:
        stats = {
            'total_batches': Batch.query.count(),
            'total_items': Item.query.count(),
            'total_offcuts': Offcut.query.count(),
            'recent_batches': [
                {
                    'batch_code': b.batch_code,
                    'batch_date': b.batch_date.strftime('%Y-%m-%d')
                }
                for b in Batch.query.order_by(Batch.batch_date.desc()).limit(5)
            ]
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
