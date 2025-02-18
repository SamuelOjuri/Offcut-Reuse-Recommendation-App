from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_talisman import Talisman
import os
from datetime import timedelta

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://offcut-recommender.netlify.app"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True,
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "max_age": 3600
    }
})

Talisman(app, 
    force_https=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
        'font-src': "'self' https://fonts.gstatic.com",
        'img-src': "'self' data: https:",
    }
)

app.config.from_object('backend.config.Config')

# Set session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,  # True for HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',  # Allow cross-site cookie sending
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=5),
    SESSION_FILE_THRESHOLD=100
)

# Set secret key with fallback to ensure it's always set
app.secret_key = app.config.get('SECRET_KEY') or os.urandom(32)

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Import routes
from backend.routes.batch_routes import batch_bp
from backend.routes.item_routes import item_bp
from backend.routes.offcut_routes import offcut_bp
from backend.routes.recommendation_routes import recommendation_bp
from backend.api.chat import chat_bp 
from backend.routes.visualization_routes import visualization_bp
from backend.routes.reports_routes import reports_bp
from backend.routes.admin_routes import admin_bp
       

# Register blueprints
app.register_blueprint(batch_bp, url_prefix='/api/batches')
app.register_blueprint(item_bp, url_prefix='/api/items')
app.register_blueprint(offcut_bp, url_prefix='/api/offcuts')
app.register_blueprint(recommendation_bp, url_prefix='/api/recommendations')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(visualization_bp, url_prefix='/api/visualizations')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(admin_bp, url_prefix='/api/admin')


if __name__ == '__main__':
    app.run(debug=True)
