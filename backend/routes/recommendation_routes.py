# routes/recommendation_routes.py

from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models import Offcut, BatchOffcutSuggestion, OffcutUsageHistory, BatchDetail, BatchItem, Batch
from backend.schemas import BatchOffcutSuggestionSchema
from backend.recommendation_engine import get_recommendations
from datetime import datetime

recommendation_bp = Blueprint('recommendation_bp', __name__)
batch_offcut_suggestion_schema = BatchOffcutSuggestionSchema()
batch_offcut_suggestions_schema = BatchOffcutSuggestionSchema(many=True)

@recommendation_bp.route('/start', methods=['POST'])
def start_recommendations():
    """Prepare data and start recommendations based on batch_code."""
    # Get the batch_code from the request JSON
    data = request.get_json()
    batch_code = data.get("batch_code")

    if not batch_code:
        return jsonify({"error": "batch_code is required"}), 400

    # Prepare the recommendation request data
    try:
        request_data = prepare_recommendation_request(batch_code)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Call the recommend_offcuts function with the prepared data
    return recommend_offcuts_internal(request_data)

def prepare_recommendation_request(batch_code):
    # Step 1: Retrieve the batch_id for the current batch code
    batch = Batch.query.filter_by(batch_code=batch_code).first()
    if not batch:
        raise Exception(f"No batch found with code {batch_code}")
    batch_id = batch.batch_id

    # Step 2: Query batch_items to get material profiles and lengths for cutting instructions
    items = BatchItem.query.filter_by(batch_id=batch_id).all()
    if not items:
        raise Exception(f"No items found for batch_id {batch_id}")

    # Step 3: Construct the cutting instructions list
    cutting_instructions = [
        {
            "material_profile": item.item.item_description,
            "required_length": item.input_bar_length_mm,
            "double_cut": item.double_cut
        }
        for item in items if item.input_bar_length_mm > 0
    ]

    # Step 4: Prepare the full request data
    request_data = {
        "batch_id": batch_id,
        "cutting_instructions": cutting_instructions
    }

    return request_data

def recommend_offcuts_internal(request_data):
    """Internal function to return offcut recommendations without updating the database."""
    # Extract data from the prepared request_data
    batch_id = request_data.get('batch_id')
    cutting_instructions = request_data.get('cutting_instructions')

    try:
        # Call the recommendation engine
        recommendations = get_recommendations(cutting_instructions)
        
        # Return recommendations without saving to database
        return jsonify({
            'batch_id': batch_id,
            'recommendations': recommendations,
            'message': f'Found {len(recommendations)} potential offcut matches'
        }), 200

    except Exception as e:
        print(f"Recommendation error: {e}")
        return jsonify({
            'error': 'Failed to generate recommendations',
            'details': str(e)
        }), 500

@recommendation_bp.route('/', methods=['POST'])
def recommend_offcuts():
    """Generate offcut recommendations based on cutting instructions."""
    data = request.get_json()

    # Validate input data
    batch_id = data.get('batch_id')
    cutting_instructions = data.get('cutting_instructions')  # Should be a list of dicts

    if not batch_id or not cutting_instructions:
        return jsonify({'error': 'batch_id and cutting_instructions are required'}), 400

    # Reuse the internal function for direct call compatibility
    return recommend_offcuts_internal(data)

@recommendation_bp.route('/confirm', methods=['POST'])
def confirm_recommendations():
    """Confirm selected recommendations and update database."""
    data = request.get_json()
    batch_id = data.get('batch_id')
    recommendations = data.get('recommendations')

    if not batch_id or not recommendations:
        return jsonify({'error': 'batch_id and recommendations are required'}), 400

    try:
        # Save confirmed recommendations to BatchOffcutSuggestion
        suggestions = []
        for rec in recommendations:
            suggestion = BatchOffcutSuggestion(
                batch_id=batch_id,
                offcut_legacy_id_1=rec.get('offcut_id'),
                matched_profile=rec.get('matched_profile'),
                suggested_length_mm=rec.get('suggested_length')
            )
            db.session.add(suggestion)
            suggestions.append(suggestion)

            # Update Offcut status
            offcut = Offcut.query.get(rec.get('offcut_id'))
            if offcut:
                offcut.is_available = False
                offcut.reuse_count += 1
                
                # Create usage history entry
                usage_history = OffcutUsageHistory(
                    offcut_id=offcut.offcut_id,
                    batch_id=batch_id,
                    reuse_success=True
                )
                db.session.add(usage_history)

        db.session.commit()
        return jsonify({
            'message': 'Recommendations confirmed and saved successfully',
            'suggestions': batch_offcut_suggestions_schema.dump(suggestions)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to save recommendations',
            'details': str(e)
        }), 500

