from datetime import datetime
from . import db
from .user import User

class TelegramUser(db.Model):
    __tablename__ = 'telegram_users'

    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(32))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    language_code = db.Column(db.String(10))
    
    # Link to base user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('telegram_user', uselist=False))
    
    # Telegram-specific fields
    is_bot = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tutorial and onboarding state
    onboarding_completed = db.Column(db.Boolean, default=False)
    tutorial_state = db.Column(db.String(50))
    
    def __init__(self, telegram_id, username=None, first_name=None, last_name=None, language_code=None):
        self.telegram_id = telegram_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.language_code = language_code
        
    def update_last_interaction(self):
        self.last_interaction = datetime.utcnow()
        db.session.commit()
        
    def complete_onboarding(self):
        self.onboarding_completed = True
        self.tutorial_state = 'completed'
        db.session.commit()