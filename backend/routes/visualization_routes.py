from flask import Blueprint, request, jsonify
from backend.graph import create_visualization
import logging

visualization_bp = Blueprint('visualization_bp', __name__)

@visualization_bp.route('/create', methods=['POST'])
def create_visualization_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
            
        query_prompt = data.get('query_prompt')
        if not query_prompt:
            return jsonify({'error': 'No query prompt provided'}), 400
            
        logging.info(f"Creating visualization for prompt: {query_prompt}")
        figure = create_visualization(query_prompt)
        
        if not figure:
            return jsonify({'error': 'No visualization data generated'}), 500
            
        return jsonify({'figure': figure})
        
    except Exception as e:
        logging.error(f"Error creating visualization: {str(e)}")
        return jsonify({'error': str(e)}), 500