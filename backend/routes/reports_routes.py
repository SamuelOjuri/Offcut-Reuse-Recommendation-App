from flask import Blueprint, jsonify, request
from backend.app import db
from backend.models import Item, BatchItem, Offcut, Batch, BatchDetail
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
            Offcut.legacy_offcut_id,
            func.count(Offcut.offcut_id).label('quantity')
        ).filter(
            Offcut.is_available == True
        ).group_by(
            Offcut.material_profile,
            Offcut.length_mm,
            Offcut.legacy_offcut_id
        ).order_by(
            Offcut.material_profile,
            Offcut.length_mm.desc()
        ).all()

        results = [
            {
                'material_profile': row[0],
                'length_mm': row[1],
                'legacy_offcut_id': row[2],
                'quantity': row[3]
            }
            for row in query
        ]

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/items', methods=['GET'])
def get_items_report():
    """Retrieve a list of all items with their codes and descriptions."""
    try:
        query = db.session.query(
            Item.item_code,
            Item.item_description
        ).order_by(Item.item_description).all()

        results = [
            {
                'item_code': row[0] or 'N/A',  # Handle NULL item codes
                'item_description': row[1]
            }
            for row in query
        ]

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/batches', methods=['GET'])
def get_batch_report():
    """Retrieve batch report for a date range."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400

        query = db.session.query(
            Batch.batch_code,
            Batch.batch_date,
            BatchDetail.saw_name,
            Item.item_code,
            Item.item_description,
            BatchItem.quantity,
            BatchItem.input_bar_length_mm,
            BatchItem.bar_length_used_mm,
            BatchItem.total_length_used_mm,
            BatchItem.offcut_length_created_mm,
            BatchItem.total_offcut_length_created_mm,
            BatchItem.double_cut,
            BatchItem.waste_percentage,
            BatchItem.usage_efficiency,
            BatchDetail.source_file
        ).join(
            BatchDetail, Batch.batch_id == BatchDetail.batch_id
        ).join(
            BatchItem, (Batch.batch_id == BatchItem.batch_id) & 
                      (BatchDetail.batch_detail_id == BatchItem.batch_items_id)
        ).join(
            Item, BatchItem.item_id == Item.item_id
        ).filter(
            Batch.batch_date.between(start_date, end_date)
        ).order_by(
            Batch.batch_date.desc()
        ).all()

        results = [
            {
                'batch_code': row[0],
                'batch_date': row[1].strftime('%Y-%m-%d'),
                'saw_name': row[2],
                'item_code': row[3],
                'item_description': row[4],
                'quantity': int(row[5]) if row[5] else 0,
                'input_length': int(row[6]) if row[6] else 0,
                'bar_length': int(row[7]) if row[7] else 0,
                'used_length': int(row[8]) if row[8] else 0,
                'offcut_length': int(row[9]) if row[9] else 0,
                'total_offcut_length': int(row[10]) if row[10] else 0,
                'double_cut': bool(row[11]) if row[11] is not None else False,
                'waste_percentage': float(row[12]) if row[12] else 0,
                'efficiency': float(row[13]) if row[13] else 0,
                'source_file': row[14]
            }
            for row in query
        ]

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500