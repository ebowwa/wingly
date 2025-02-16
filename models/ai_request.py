from datetime import datetime
from typing import Optional, Dict, Union, Any
from . import db

class AIRequest(db.Model):
    __tablename__ = 'ai_requests'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=True)  # Default to True
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    endpoint: Optional[str] = db.Column(db.String)
    prompt_type: Optional[str] = db.Column(db.String)
    response_schema: Optional[str] = db.Column(db.String)
    expected_variables: Optional[str] = db.Column(db.String)
    input_text: Optional[str] = db.Column(db.Text)
    input_audio_url: Optional[str] = db.Column(db.String)
    output_text: Optional[str] = db.Column(db.Text)
    output_audio_url: Optional[str] = db.Column(db.String)
    duration_ms: Optional[int] = db.Column(db.Integer)
    tokens_used: Optional[int] = db.Column(db.Integer)
    model_version: Optional[str] = db.Column(db.String)
    status: Optional[str] = db.Column(db.String)
    error: Optional[str] = db.Column(db.Text)
    ai_model: Optional[str] = db.Column(db.String)
    temperature: Optional[float] = db.Column(db.Float)
    top_p: Optional[float] = db.Column(db.Float)
    top_k: Optional[int] = db.Column(db.Integer)
    max_output_tokens: Optional[int] = db.Column(db.Integer)
    step_variables: Optional[str] = db.Column(db.String)
    chat_history: Optional[str] = db.Column(db.Text)

    def to_gemini_request(self) -> Dict[str, Any]:
        """Convert AIRequest to GeminiRequest format"""
        return {
            "role": "user",
            "content": {
                "parts": [
                    {
                        "text": self.input_text
                    } if self.input_text else {
                        "inline_data": {
                            "mime_type": "audio/ogg",
                            "data": self.input_audio_url
                        }
                    }
                ]
            }
        }

    # Add relationship (optional)
    profile = db.relationship('Profile', backref=db.backref('ai_requests', lazy=True), foreign_keys=[profile_id])

    def __init__(self, **kwargs):
        # Allow initialization without a profile
        super(AIRequest, self).__init__(**kwargs)

class MediaAsset(db.Model):
    __tablename__ = 'media_assets'
    
    id: int = db.Column(db.Integer, primary_key=True)
    memory_id: int = db.Column(db.Integer, db.ForeignKey('memories.id'), nullable=False)
    asset_type: Optional[str] = db.Column(db.String)
    url: Optional[str] = db.Column(db.String)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    asset_metadata: Optional[str] = db.Column(db.Text)
    original_filename: Optional[str] = db.Column(db.String)
    mime_type: Optional[str] = db.Column(db.String)
    size_bytes: Optional[int] = db.Column(db.Integer)