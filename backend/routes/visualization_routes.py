from flask import Blueprint, request, jsonify, make_response
from backend.graph import create_visualization
import logging

visualization_bp = Blueprint('visualization_bp', __name__)

@visualization_bp.route('/generate', methods=['POST'])
def create_visualization_route():
    try:
        data = request.get_json()
        if not data:
            return make_response(jsonify({'error': 'No JSON data received'}), 400)
            
        query = data.get('query')
        if not query:
            return make_response(jsonify({'error': 'No query provided'}), 400)
            
        logging.info(f"Creating visualization for prompt: {query}")
        figure = create_visualization(query)
        
        if not figure:
            return make_response(jsonify({'error': 'No visualization data generated'}), 500)
            
        response = make_response(jsonify({'figure': figure}))
        return response
        
    except Exception as e:
        logging.error(f"Error creating visualization: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)