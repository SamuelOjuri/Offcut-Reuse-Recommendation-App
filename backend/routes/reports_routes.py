from flask import Blueprint, jsonify
from backend.app import db
from backend.models import Item, BatchItem, Offcut
from sqlalchemy import func

reports_bp = Blueprint('reports_bp', __name__)

@reports_bp.route('/summary', methods=['GET'])
def get_summary_metrics():
    """Retrieve summary metrics for materials usage."""
    try:
        query = db.session.query(
            Item.item_description,
            Item.item_code,
            func.sum(BatchItem.input_bar_length_mm * BatchItem.quantity).label('total_input_length'),
            func.sum(BatchItem.total_length_used_mm).label('total_used_length'),
            func.sum(BatchItem.total_offcut_length_created_mm).label('total_offcut_length'),
            func.avg(BatchItem.usage_efficiency).label('avg_efficiency'),
            func.avg(BatchItem.waste_percentage).label('avg_waste')
        ).join(BatchItem).group_by(Item.item_description, Item.item_code).all()

        # Convert query results to list of dictionaries
        results = [
            {
                'item_description': row[0],
                'item_code': row[1],
                'total_input_length': float(row[2]) if row[2] else 0,
                'total_used_length': float(row[3]) if row[3] else 0,
                'total_offcut_length': float(row[4]) if row[4] else 0,
                'avg_efficiency': float(row[5]) if row[5] else 0,
                'avg_waste': float(row[6]) if row[6] else 0
            }
            for row in query
        ]

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/offcuts', methods=['GET'])
def get_offcuts_inventory():
    """Retrieve available offcuts inventory."""
    try:
        query = db.session.query(
            Offcut.material_profile,
            Offcut.length_mm,
            func.count(Offcut.offcut_id).label('quantity')
        ).filter(
            Offcut.is_available == True
        ).group_by(
            Offcut.material_profile,
            Offcut.length_mm
        ).order_by(
            Offcut.material_profile,
            Offcut.length_mm.desc()
        ).all()

        results = [
            {
                'material_profile': row[0],
                'length_mm': row[1],
                'quantity': row[2]
            }
            for row in query
        ]

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
