from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.config.from_object('backend.config.Config')
#app.config.from_object('config.Config')

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Import routes
from backend.routes.batch_routes import batch_bp
from backend.routes.item_routes import item_bp
from backend.routes.offcut_routes import offcut_bp
from backend.routes.recommendation_routes import recommendation_bp

# Register blueprints
app.register_blueprint(batch_bp, url_prefix='/api/batches')
app.register_blueprint(item_bp, url_prefix='/api/items')
app.register_blueprint(offcut_bp, url_prefix='/api/offcuts')
app.register_blueprint(recommendation_bp, url_prefix='/api/recommendations')

if __name__ == '__main__':
    app.run(debug=True)
