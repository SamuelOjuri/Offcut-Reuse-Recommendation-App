from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "supports_credentials": True,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }
})

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
