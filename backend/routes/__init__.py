# routes/__init__.py

from backend.routes.batch_routes import batch_bp
from backend.routes.item_routes import item_bp
from backend.routes.offcut_routes import offcut_bp
from backend.routes.recommendation_routes import recommendation_bp

__all__ = ['batch_bp', 'item_bp', 'offcut_bp', 'recommendation_bp']
