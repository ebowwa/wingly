from datetime import datetime
from . import db
from .ai_request import AIRequest
from .memory import Memory, memory_owners, memory_shares

class Profile(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # Use string reference instead of direct import
    user = db.relationship('User', back_populates='profile')
    
    # Telegram user relationship - use string reference
    telegram_user_id = db.Column(db.Integer, db.ForeignKey('telegram_users.id'))
    telegram_user = db.relationship('TelegramUser', back_populates='profile')

    # Core Profile Data
    preferred_languages = db.Column(db.String(50))
    timezone = db.Column(db.String(50))

    # Personality Data
    interests = db.Column(db.JSON)
    vision = db.Column(db.Text)
    vibe = db.Column(db.Text)
    goals = db.Column(db.JSON)
    values = db.Column(db.JSON)
    preferences = db.Column(db.JSON)

    # Settings
    notification_preferences = db.Column(db.JSON)
    privacy_settings = db.Column(db.JSON)
    voice_preferences = db.Column(db.JSON)

    # Relationships
    # Relationships with proper back_populates
    # Relationships with string references
    ai_requests = db.relationship('AIRequest',
                                back_populates='profile',
                                lazy='dynamic')
    
    memories = db.relationship('Memory',
                             back_populates='profile',
                             overlaps="owner_profiles,shared_profiles")
    
    tutorial_memories = db.relationship('TutorialMemory',
                                      back_populates='profile')

    owned_memories = db.relationship('Memory',
                                   secondary=memory_owners,
                                   back_populates='owner_profiles',
                                   overlaps="memories")

    memory_shares = db.relationship('Memory',
                                  secondary=memory_shares,
                                  back_populates='shared_profiles',
                                  overlaps="memories")
