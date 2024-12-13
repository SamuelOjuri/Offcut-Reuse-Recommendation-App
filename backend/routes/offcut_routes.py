# routes/offcut_routes.py

from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models import Offcut
from backend.schemas import OffcutSchema

offcut_bp = Blueprint('offcut_bp', __name__)
offcut_schema = OffcutSchema()
offcuts_schema = OffcutSchema(many=True)

@offcut_bp.route('/', methods=['GET'])
def get_offcuts():
    """Retrieve all offcuts."""
    offcuts = Offcut.query.all()
    result = offcuts_schema.dump(offcuts)
    return jsonify(result), 200

@offcut_bp.route('/available', methods=['GET'])
def get_available_offcuts():
    """Retrieve available offcuts based on material profile and length."""
    material_profile = request.args.get('material_profile')
    length = request.args.get('length', type=int)

    query = Offcut.query.filter_by(is_available=True)

    if material_profile:
        query = query.filter_by(material_profile=material_profile)
    if length:
        query = query.filter(Offcut.length >= length)

    offcuts = query.order_by(Offcut.length.asc()).all()
    result = offcuts_schema.dump(offcuts)
    return jsonify(result), 200

@offcut_bp.route('/', methods=['POST'])
def create_offcut():
    """Create a new offcut."""
    data = request.get_json()
    errors = offcut_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    new_offcut = Offcut(
        legacy_offcut_id=data.get('legacy_offcut_id'),
        length=data['length'],
        material_profile=data['material_profile'],
        is_available=data.get('is_available', True),
        reuse_count=data.get('reuse_count', 0),
        batch_detail_id=data['batch_detail_id']
    )
    db.session.add(new_offcut)
    db.session.commit()
    result = offcut_schema.dump(new_offcut)
    return jsonify(result), 201

@offcut_bp.route('/<int:id>', methods=['GET'])
def get_offcut(id):
    """Retrieve an offcut by ID."""
    offcut = Offcut.query.get_or_404(id)
    result = offcut_schema.dump(offcut)
    return jsonify(result), 200

@offcut_bp.route('/<int:id>', methods=['PUT'])
def update_offcut(id):
    """Update an offcut."""
    offcut = Offcut.query.get_or_404(id)
    data = request.get_json()
    errors = offcut_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    if 'legacy_offcut_id' in data:
        offcut.legacy_offcut_id = data['legacy_offcut_id']
    if 'length' in data:
        offcut.length = data['length']
    if 'material_profile' in data:
        offcut.material_profile = data['material_profile']
    if 'is_available' in data:
        offcut.is_available = data['is_available']
    if 'reuse_count' in data:
        offcut.reuse_count = data['reuse_count']
    if 'batch_detail_id' in data:
        offcut.batch_detail_id = data['batch_detail_id']
    db.session.commit()
    result = offcut_schema.dump(offcut)
    return jsonify(result), 200

@offcut_bp.route('/<int:id>/status', methods=['PUT'])
def update_offcut_status(id):
    """Update the availability status of an offcut."""
    offcut = Offcut.query.get_or_404(id)
    data = request.get_json()
    is_available = data.get('is_available')

    if is_available is None:
        return jsonify({'error': 'is_available field is required'}), 400

    offcut.is_available = is_available
    db.session.commit()
    result = offcut_schema.dump(offcut)
    return jsonify(result), 200

@offcut_bp.route('/<int:id>', methods=['DELETE'])
def delete_offcut(id):
    """Delete an offcut."""
    offcut = Offcut.query.get_or_404(id)
    db.session.delete(offcut)
    db.session.commit()
    return '', 204



