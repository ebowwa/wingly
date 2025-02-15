from datetime import datetime
from models.user import db, User

class AdminRole(db.Model):
    """Admin role model for managing admin permissions."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    """Admin model extending base User model."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('admin_role.id'), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref=db.backref('admin', uselist=False))
    role = db.relationship('AdminRole', backref='admins')

    def __init__(self, user, role, is_super_admin=False):
        self.user_id = user.id
        self.role_id = role.id
        self.is_super_admin = is_super_admin