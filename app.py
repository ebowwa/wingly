# hanldes the flask auth and fastapi routes
import os
from dotenv import load_dotenv

load_dotenv()
import logging
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from services.s3 import s3_service

from routers.auth_router import auth_router, jwt
# from routers.admin_router import admin_router
from routers.gemini_router import gemini_router
from models.user import db, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()])

# Set specific logging levels
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
app = Flask(__name__)
fastapi_app = FastAPI()
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',
                                                  'sqlite:///./app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY',
                                         'your-secret-key-change-this')

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# Register blueprints (only once)
app.register_blueprint(auth_router, url_prefix='/auth')
# app.register_blueprint(admin_router, url_prefix='/admin')

# Register FastAPI routers
fastapi_app.include_router(gemini_router, prefix="/api")
fastapi_app.mount("/", WSGIMiddleware(app))


def init_s3():
  """Initialize S3 connection."""
  try:
    logger.info("Testing S3 connectivity...")
    s3_service.s3_client
    logger.info("Successfully initialized S3 service")
  except Exception as e:
    logger.error(f"Error during S3 initialization: {e}")
    raise


# Initialize services after defining them
with app.app_context():
  # Check if database needs to be initialized
  inspector = db.inspect(db.engine)
  if not inspector.get_table_names():
    logger.info("Initializing database tables...")
    db.create_all()
    logger.info("Database tables created successfully")
  else:
    logger.info("Database tables already exist")

  # Initialize S3 after database setup
  init_s3()

if __name__ == '__main__':
  import uvicorn
  uvicorn.run("app:fastapi_app",
              host=os.getenv('FLASK_HOST', '0.0.0.0'),
              port=int(os.getenv('FLASK_PORT', 8080)),
              reload=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
              log_level="info")
