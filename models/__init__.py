from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

# Import models in order of dependencies
from .user import User
from .memory import Memory  # Add this import
from .profile import Profile
from .ai_request import AIRequest
from .friendship import Friendship  # Add this if not already imported