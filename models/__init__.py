
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

# Import models in dependency order
from .user import User  # User must be first since other models depend on it
from .profile import Profile  # Profile depends on User
from .memory import Memory  # Memory depends on Profile
from .media_asset import MediaAsset  # MediaAsset depends on Memory
from .ai_request import AIRequest  # AIRequest depends on Profile
from .friendship import Friendship  # Friendship depends on User
from .tutorial_memory import TutorialMemory  # TutorialMemory depends on Profile, MediaAsset, and AIRequest
