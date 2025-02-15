from datetime import datetime
from . import db

class MediaAsset(db.Model):
    __tablename__ = 'media_assets'
    
    id = db.Column(db.Integer, primary_key=True)
    memory_id = db.Column(db.Integer, db.ForeignKey('memories.id'), nullable=False)
    asset_type = db.Column(db.String)
    url = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    asset_metadata = db.Column(db.String)  # Changed from 'metadata'
    original_filename = db.Column(db.String)
    mime_type = db.Column(db.String)
    size_bytes = db.Column(db.Integer)