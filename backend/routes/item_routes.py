# routes/item_routes.py

from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models import Item
from backend.schemas import ItemSchema

item_bp = Blueprint('item_bp', __name__)
item_schema = ItemSchema()
items_schema = ItemSchema(many=True)

@item_bp.route('/', methods=['GET'])
def get_items():
    """Retrieve all items."""
    items = Item.query.all()
    result = items_schema.dump(items)
    return jsonify(result), 200

@item_bp.route('/', methods=['POST'])
def create_item():
    """Create a new item."""
    data = request.get_json()
    errors = item_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    new_item = Item(
        item_code=data['item_code'],
        description=data.get('description')
    )
    db.session.add(new_item)
    db.session.commit()
    result = item_schema.dump(new_item)
    return jsonify(result), 201

@item_bp.route('/<int:id>', methods=['GET'])
def get_item(id):
    """Retrieve an item by ID."""
    item = Item.query.get_or_404(id)
    result = item_schema.dump(item)
    return jsonify(result), 200

@item_bp.route('/<int:id>', methods=['PUT'])
def update_item(id):
    """Update an item."""
    item = Item.query.get_or_404(id)
    data = request.get_json()
    errors = item_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    if 'item_code' in data:
        item.item_code = data['item_code']
    if 'description' in data:
        item.description = data['description']
    db.session.commit()
    result = item_schema.dump(item)
    return jsonify(result), 200

@item_bp.route('/<int:id>', methods=['DELETE'])
def delete_item(id):
    """Delete an item."""
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return '', 204
