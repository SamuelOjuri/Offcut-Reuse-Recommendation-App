from flask import Blueprint, request, jsonify, make_response
from backend.graph import create_visualization
import logging

visualization_bp = Blueprint('visualization_bp', __name__)

@visualization_bp.route('/generate', methods=['OPTIONS'])
def handle_preflight():
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', 'https://offcut-recommender.netlify.app')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

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
        response.headers.add('Access-Control-Allow-Origin', 'https://offcut-recommender.netlify.app')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        logging.error(f"Error creating visualization: {str(e)}")
        error_response = make_response(jsonify({'error': str(e)}), 500)
        error_response.headers.add('Access-Control-Allow-Origin', 'https://offcut-recommender.netlify.app')
        error_response.headers.add('Access-Control-Allow-Credentials', 'true')
        return error_response