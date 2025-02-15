from datetime import datetime
from . import db

class Friendship(db.Model):
    __tablename__ = 'friendships'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    became_friends_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    interaction_streak = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.CheckConstraint('user_id < friend_id', name='friendship_order_check'),
    )