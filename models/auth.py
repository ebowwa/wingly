from datetime import datetime
from . import db, bcrypt

class AdminRole(db.Model):
    """Admin role model for managing admin permissions."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    """Admin model extending base User model."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)  # Match users table name
    role_id = db.Column(db.Integer, db.ForeignKey('admin_role.id'), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', back_populates='admin')  # Use back_populates for explicit relationship
    role = db.relationship('AdminRole', backref='admins')

    def __init__(self, user, role, is_super_admin=False):
        self.user_id = user.id
        self.role_id = role.id
        self.is_super_admin = is_super_admin


from datetime import datetime, timedelta
# Import Profile model at the module level to avoid circular imports
class User(db.Model):
    __tablename__ = 'users'
    
    # AUTH
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')
    
    # Social Relationships
    friends = db.relationship(
        'User', secondary='friendships',
        primaryjoin='User.id==friendships.c.user_id',
        secondaryjoin='User.id==friendships.c.friend_id',
        backref=db.backref('friended_by', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # Updated Social Relationships
    friendships = db.relationship('Friendship',
        primaryjoin='or_(User.id==Friendship.user_id, User.id==Friendship.friend_id)',
        lazy='dynamic'
    )
    
    # Update the profile relationship with explicit foreign_keys
    profile = db.relationship('Profile', 
                            backref='user', 
                            uselist=False,
                            foreign_keys='Profile.user_id')
    
    subscription = db.relationship('Subscription', backref='user', uselist=False)
    
    def add_friend(self, user):
        if self.id == user.id:
            raise ValueError("Cannot befriend yourself")
        
        user_id, friend_id = sorted([self.id, user.id])
        if not self.is_friend(user):
            friendship = Friendship(user_id=user_id, friend_id=friend_id)
            db.session.add(friendship)
            db.session.commit()
            
    def remove_friend(self, user):
        user_id, friend_id = sorted([self.id, user.id])
        friendship = Friendship.query.filter_by(
            user_id=user_id, 
            friend_id=friend_id
        ).first()
        if friendship:
            db.session.delete(friendship)
            db.session.commit()
            
    def is_friend(self, user):
        user_id, friend_id = sorted([self.id, user.id])
        return Friendship.query.filter_by(
            user_id=user_id,
            friend_id=friend_id
        ).first() is not None
    
    def get_friendship_duration(self, friend):
        """Returns the duration of friendship in days"""
        if not self.is_friend(friend):
            return 0
        
        user_id, friend_id = sorted([self.id, friend.id])
        friendship = Friendship.query.filter_by(
            user_id=user_id,
            friend_id=friend_id
        ).first()
        
        if friendship:
            return (datetime.utcnow() - friendship.became_friends_at).days
        return 0
    
    def get_interaction_streak(self, friend):
        """Returns the current daily interaction streak with friend"""
        if not self.is_friend(friend):
            return 0
            
        user_id, friend_id = sorted([self.id, friend.id])
        friendship = Friendship.query.filter_by(
            user_id=user_id,
            friend_id=friend_id
        ).first()
        
        if not friendship:
            return 0
            
        if (datetime.utcnow() - friendship.last_interaction) > timedelta(days=1):
            return 0
            
        return friendship.interaction_streak
    
    def record_interaction(self, friend):
        """Record an interaction with friend and update streak"""
        if not self.is_friend(friend):
            return
            
        user_id, friend_id = sorted([self.id, friend.id])
        friendship = Friendship.query.filter_by(
            user_id=user_id,
            friend_id=friend_id
        ).first()
        
        if friendship:
            now = datetime.utcnow()
            if (now - friendship.last_interaction) <= timedelta(days=1):
                friendship.interaction_streak += 1
            else:
                friendship.interaction_streak = 1
            
            friendship.last_interaction = now
            db.session.commit()

    def set_password(self, password):
        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")
            
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
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
