from backend.app import db, ma
from sqlalchemy.sql import func

class Batch(db.Model):
    __tablename__ = 'batches'
    batch_id = db.Column(db.Integer, primary_key=True)
    batch_code = db.Column(db.String(50), unique=True, nullable=False)
    batch_date = db.Column(db.Date, nullable=False)
    details = db.relationship('BatchDetail', backref='batch', lazy=True)
    items = db.relationship('BatchItem', backref='batch', lazy=True)

class BatchDetail(db.Model):
    __tablename__ = 'batch_details'
    batch_detail_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id', ondelete='CASCADE'), nullable=False)
    saw_name = db.Column(db.String(50))
    source_file = db.Column(db.Text)

class Item(db.Model):
    __tablename__ = 'items'
    item_id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50))
    item_description = db.Column(db.Text, unique=True, nullable=False)
    batch_items = db.relationship('BatchItem', backref='item', lazy=True)

class Offcut(db.Model):
    __tablename__ = 'offcuts'
    offcut_id = db.Column(db.Integer, primary_key=True)
    legacy_offcut_id = db.Column(db.Integer, unique=True, nullable=False)
    length_mm = db.Column(db.Integer, nullable=False)
    material_profile = db.Column(db.String(50))
    created_in_batch_detail_id = db.Column(db.Integer, db.ForeignKey('batch_details.batch_detail_id'))
    related_legacy_offcut_id = db.Column(db.Integer)
    is_available = db.Column(db.Boolean, default=True)
    reuse_count = db.Column(db.Integer, default=0)
    usage_history = db.relationship('OffcutUsageHistory', backref='offcut', lazy=True)

class BatchItem(db.Model):
    __tablename__ = 'batch_items'
    batch_items_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'))
    quantity = db.Column(db.Integer)
    input_bar_length_mm = db.Column(db.Integer)
    bar_length_used_mm = db.Column(db.Integer)
    total_length_used_mm = db.Column(db.Integer)
    offcut_length_created_mm = db.Column(db.Integer)
    total_offcut_length_created_mm = db.Column(db.Integer)
    double_cut = db.Column(db.Boolean)
    waste_percentage = db.Column(db.Numeric(5, 2))
    usage_efficiency = db.Column(db.Numeric(5, 2))

class BatchOffcutSuggestion(db.Model):
    __tablename__ = 'batch_offcut_suggestions'
    suggestion_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id'))
    offcut_legacy_id_1 = db.Column(db.Integer)
    offcut_legacy_id_2 = db.Column(db.Integer)
    matched_profile = db.Column(db.String(50))
    suggested_length_mm = db.Column(db.Integer)
    batch_detail_id = db.Column(db.Integer, db.ForeignKey('batch_details.batch_detail_id'))

class OffcutUsageHistory(db.Model):
    __tablename__ = 'offcut_usage_history'
    usage_id = db.Column(db.Integer, primary_key=True)
    offcut_id = db.Column(db.Integer, db.ForeignKey('offcuts.offcut_id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id'), nullable=False)
    reuse_success = db.Column(db.Boolean)
    reuse_date = db.Column(db.Date, default=func.current_date())
