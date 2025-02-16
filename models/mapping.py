from . import db
from .user import User
from .profile import Profile
from .telegram_user import TelegramUser
from .memory import Memory
from .ai_request import AIRequest

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
                                           back_populates='memory_shares')

    # AIRequest <-> Profile relationship
    AIRequest.profile = db.relationship('Profile',
                                      back_populates='ai_requests')

    # Configure all mappers
    db.configure_mappers()