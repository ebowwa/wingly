from datetime import datetime
from . import db
from .media_asset import MediaAsset

class Memory(db.Model):
    __tablename__ = 'memories'

    id = db.Column(db.Integer, primary_key=True)
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