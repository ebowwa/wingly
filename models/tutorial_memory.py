from datetime import datetime
from . import db
from .media_asset import MediaAsset
from .ai_request import AIRequest

class TutorialMemory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    step = db.Column(db.String(50))  # 'name_input', 'name_correction', 'truthnlie'
    
    # Step Data
    input_text = db.Column(db.Text)
    response_text = db.Column(db.Text)
    
    # Associated Media Asset
    media_asset_id = db.Column(db.Integer, db.ForeignKey('media_asset.id'))
    media_asset = db.relationship('MediaAsset', backref='tutorial_memories')
    
    # Associated AI Requests
    ai_request_id = db.Column(db.Integer, db.ForeignKey('ai_request.id'))
    ai_request = db.relationship('AIRequest', backref='tutorial_memory')
    
    # Metadata
    completed = db.Column(db.Boolean, default=False)
    completion_time = db.Column(db.DateTime)