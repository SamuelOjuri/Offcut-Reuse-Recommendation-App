from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_talisman import Talisman

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "https://offcut-reuse-recommendation-app.onrender.com",
            "https://offcut-recommender.netlify.app"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True,
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "max_age": 3600
    }
})

Talisman(app, 
    force_https=False,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
        'font-src': "'self' https://fonts.gstatic.com",
        'img-src': "'self' data: https:",
    }
)

app.config.from_object('backend.config.Config')

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
       

# Register blueprints
app.register_blueprint(batch_bp, url_prefix='/api/batches')
app.register_blueprint(item_bp, url_prefix='/api/items')
app.register_blueprint(offcut_bp, url_prefix='/api/offcuts')
app.register_blueprint(recommendation_bp, url_prefix='/api/recommendations')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(visualization_bp, url_prefix='/api/visualizations')
app.register_blueprint(reports_bp, url_prefix='/api/reports')


if __name__ == '__main__':
    app.run(debug=True)
