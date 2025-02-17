
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

# Import models in dependency order
from .auth import User, Admin, Friendship  # User must be first since other models depend on it
from .profile import Profile, Memory, TutorialMemory  # Profile depends on User
# from .memory import Memory, TutorialMemory  # Memory depends on Profile
from .ai_request import AIRequest, MediaAsset  # AIRequest depends on Profile
# from .friendship import Friendship  # Friendship depends on User

def configure_mappers():
    """Configure all model relationships and mappers."""
    
    # TelegramUser <-> Profile relationship
    TelegramUser.profile = db.relationship('Profile',
                                         back_populates='telegram_user',
                                         uselist=False)
    
    # User <-> Profile relationship
    User.profile = db.relationship('Profile',
                                 back_populates='user',
                                 uselist=False)
    
    # Memory <-> Profile relationships
    Memory.profile = db.relationship('Profile',
                                   back_populates='memories')
    Memory.owner_profiles = db.relationship('Profile',
                                          secondary='memory_owners',
                                          back_populates='owned_memories')
    Memory.shared_profiles = db.relationship('Profile',
                                           secondary='memory_shares',
                                           back_populates='shared_memories')
    
    # AIRequest <-> Profile relationship
    AIRequest.profile = db.relationship('Profile',
                                      back_populates='ai_requests')
    
    # Configure all mappers
    try:
        db.configure_mappers()
    except Exception as e:
        print(f"Error configuring mappers: {e}")
        raise