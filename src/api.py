from flask import Flask
from datetime import datetime, timedelta
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import logging
import os

app = Flask(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
jwt = JWTManager(app)

CORS(app)

# For more specific CORS configuration, you can use:
# CORS(app, resources={
#     r"/generate_report": {
#         "origins": ["http://localhost:3000", "https://yourdomain.com"],
#         "methods": ["POST"],
#         "allow_headers": ["Content-Type"]
#     }
# })

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints
from routes import auth_bp, research_bp, user_bp
app.register_blueprint(auth_bp)
app.register_blueprint(research_bp)
app.register_blueprint(user_bp)

if __name__ == '__main__':
    app.run(debug=True)
