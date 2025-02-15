from datetime import datetime
from . import db

# Memory association tables
memory_owners = db.Table(
    'memory_owners',
    db.Column('profile_id', db.Integer, db.ForeignKey('profiles.id')),
    db.Column('memory_id', db.Integer, db.ForeignKey('memories.id')))

memory_shares = db.Table(
    'memory_shares',
    db.Column('profile_id', db.Integer, db.ForeignKey('profiles.id')),
    db.Column('memory_id', db.Integer, db.ForeignKey('memories.id')))

from .ai_request import AIRequest
from .memory import Memory, memory_owners, memory_shares


class Profile(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

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
    # Add the relationship to AIRequest
    ai_requests = db.relationship('AIRequest',
                                  backref='profile',
                                  lazy='dynamic')
    memories = db.relationship('Memory', backref='profile')
    tutorial_memories = db.relationship('TutorialMemory', backref='profile')

    # Memory relationships
    mutual_memories = db.relationship('Memory',
                                      secondary=memory_owners,
                                      backref=db.backref('owner_profiles',
                                                         lazy='dynamic'))

    shared_memories = db.relationship('Memory',
                                      secondary=memory_shares,
                                      backref=db.backref(
                                          'shared_with_profiles',
                                          lazy='dynamic'))
