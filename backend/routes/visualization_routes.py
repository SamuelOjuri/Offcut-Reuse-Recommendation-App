from flask import Blueprint, request, jsonify, make_response, Response
from backend.graph import create_visualization
import logging
import psutil
import gc
import json
import os

visualization_bp = Blueprint('visualization_bp', __name__)



@visualization_bp.route('/generate', methods=['POST'])
def create_visualization_route():
    try:
        gc.collect()
        
        # Lower memory threshold
        mem = psutil.Process().memory_info().rss / 1024 / 1024
        if mem > 300:
            return make_response(jsonify({'error': 'Server is busy'}), 503)
            
        data = request.get_json()
        if not data or not data.get('query'):
            return make_response(jsonify({'error': 'Invalid request'}), 400)
            
        # Validate that the query is one of the predefined options
        valid_queries = [
            "Create bar charts showing total material usage over time",
            "Create a bar chart showing the top 10 materials by Total Length Used",
            "Create a bar chart showing top 10 items by total offcut length",
            "Create a visualization of top and bottom 5 materials by efficiency"
        ]
        
        if data['query'] not in valid_queries:
            return make_response(jsonify({'error': 'Invalid visualization type'}), 400)
            
        def generate():
            figure = create_visualization(data['query'])
            if figure:
                chunk_size = 8192
                figure_json = json.dumps({'figure': figure})
                
                for i in range(0, len(figure_json), chunk_size):
                    chunk = figure_json[i:i + chunk_size]
                    yield chunk
                    
        response = Response(generate(), mimetype='application/json')
        return response
        
    except Exception as e:
        logging.error(f"Visualization error: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)