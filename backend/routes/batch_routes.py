# routes/batch_routes.py

from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models import Batch
from backend.schemas import BatchSchema
from datetime import datetime

batch_bp = Blueprint('batch_bp', __name__)
batch_schema = BatchSchema()
batches_schema = BatchSchema(many=True)

@batch_bp.route('/', methods=['GET'])
def get_batches():
    """Retrieve all batches."""
    batches = Batch.query.all()
    result = batches_schema.dump(batches)
    return jsonify(result), 200

@batch_bp.route('/', methods=['POST'])
def create_batch():
    """Create a new batch."""
    data = request.get_json()
    errors = batch_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    new_batch = Batch(
        batch_code=data['batch_code'],
        date=datetime.strptime(data['date'], '%Y-%m-%d')
    )
    db.session.add(new_batch)
    db.session.commit()
    result = batch_schema.dump(new_batch)
    return jsonify(result), 201

@batch_bp.route('/<int:id>', methods=['GET'])
def get_batch(id):
    """Retrieve a batch by ID."""
    batch = Batch.query.get_or_404(id)
    result = batch_schema.dump(batch)
    return jsonify(result), 200

@batch_bp.route('/<int:id>', methods=['PUT'])
def update_batch(id):
    """Update a batch."""
    batch = Batch.query.get_or_404(id)
    data = request.get_json()
    errors = batch_schema.validate(data, partial=True)  # Allow partial updates
    if errors:
        return jsonify(errors), 400

    if 'batch_code' in data:
        batch.batch_code = data['batch_code']
    if 'date' in data:
        batch.date = datetime.strptime(data['date'], '%Y-%m-%d')
    db.session.commit()
    result = batch_schema.dump(batch)
    return jsonify(result), 200

@batch_bp.route('/<int:id>', methods=['DELETE'])
def delete_batch(id):
    """Delete a batch."""
    batch = Batch.query.get_or_404(id)
    db.session.delete(batch)
    db.session.commit()
    return '', 204

@batch_bp.route('/check/<batch_code>', methods=['GET'])
def check_batch_exists(batch_code):
    """Check if a batch code exists in the database."""
    batch = Batch.query.filter_by(batch_code=batch_code).first()
    return jsonify({
        'exists': batch is not None
    }), 200
