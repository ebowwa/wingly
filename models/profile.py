from datetime import datetime
from . import db
# from .media_asset import MediaAsset

class Memory(db.Model):
    __tablename__ = 'memories'

    id = db.Column(db.Integer, primary_key=True)
    memory_type = db.Column(db.String(50))  # Added missing column     
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'))

    # Relationships
    owners = db.relationship(
        'Profile',
        secondary='memory_owners',
        backref=db.backref('mutual_memories', lazy='dynamic')
    )

    shared_with = db.relationship(
        'Profile',
        secondary='memory_shares',
        backref=db.backref('shared_memories', lazy='dynamic')
    )

    # Media assets relationship
    media_assets = db.relationship('MediaAsset', backref='memory', lazy='dynamic')

    visibility = db.Column(db.String(20), default='mutual')
    is_shared = db.Column(db.Boolean, default=False)

    @classmethod
    def create_mutual_memory(cls, profiles):
        memory = cls(visibility='mutual')
        for profile in profiles:
            memory.owners.append(profile)
        return memory

    def share_with_friend(self, friend_profile):
        if friend_profile not in self.shared_with:
            self.shared_with.append(friend_profile)
            self.is_shared = True

    def unshare_with_friend(self, friend_profile):
        if friend_profile in self.shared_with:
            self.shared_with.remove(friend_profile)
            if len(self.shared_with) == 0:
                self.is_shared = False

# Define association tables after Memory model
memory_owners = db.Table(
    'memory_owners',
    db.Column('profile_id', db.Integer, db.ForeignKey('profiles.id')),
    db.Column('memory_id', db.Integer, db.ForeignKey('memories.id'))
)

memory_shares = db.Table(
    'memory_shares',
    db.Column('profile_id', db.Integer, db.ForeignKey('profiles.id')),
    db.Column('memory_id', db.Integer, db.ForeignKey('memories.id'))
)


class TutorialMemory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    step = db.Column(db.String(50))  # 'name_input', 'name_correction', 'truthnlie'
    
    # Step Data
    input_text = db.Column(db.Text)
    response_text = db.Column(db.Text)
    
    # Associated Media Asset
    media_asset_id = db.Column(db.Integer, db.ForeignKey('media_assets.id'))
    media_asset = db.relationship('MediaAsset', backref='tutorial_memories')
    
    # Associated AI Requests
    ai_request_id = db.Column(db.Integer, db.ForeignKey('ai_requests.id'))
    ai_request = db.relationship('AIRequest', backref='tutorial_memory')
    
    # Metadata
    completed = db.Column(db.Boolean, default=False)
    completion_time = db.Column(db.DateTime)

from datetime import datetime
from . import db
from .ai_request import AIRequest

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
