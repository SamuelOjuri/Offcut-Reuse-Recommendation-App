from flask import Blueprint, request, jsonify
from backend.graph import create_visualization
import logging

visualization_bp = Blueprint('visualization_bp', __name__)

@visualization_bp.route('/generate', methods=['POST'])
def create_visualization_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
            
        query = data.get('query')
        if not query:
            return jsonify({'error': 'No query provided'}), 400
            
        logging.info(f"Creating visualization for prompt: {query}")
        figure = create_visualization(query)
        
        if not figure:
            return jsonify({'error': 'No visualization data generated'}), 500
            
        return jsonify({'figure': figure})
        
    except Exception as e:
        logging.error(f"Error creating visualization: {str(e)}")
        return jsonify({'error': str(e)}), 500