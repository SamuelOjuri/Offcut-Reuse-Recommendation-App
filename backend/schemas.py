from backend.app import ma
from backend.models import Batch, BatchDetail, Item, Offcut, BatchItem, BatchOffcutSuggestion, OffcutUsageHistory

class BatchSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Batch
        include_fk = True

class BatchDetailSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BatchDetail
        include_fk = True

class ItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Item
        include_fk = True

class OffcutSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Offcut
        include_fk = True

class BatchItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BatchItem
        include_fk = True

class BatchOffcutSuggestionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BatchOffcutSuggestion
        include_fk = True

class OffcutUsageHistorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OffcutUsageHistory
        include_fk = True
