from flask import Blueprint, Response, request, stream_with_context
from backend.chat_agent import stream_final_answer

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/stream', methods=['POST'])
def chat_stream():
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return {'error': 'No prompt provided'}, 400

    def generate():
        for chunk in stream_final_answer(prompt):
            yield chunk

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    ) 