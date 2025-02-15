from datetime import datetime
from . import db

class AIRequest(db.Model):
    __tablename__ = 'ai_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'))
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    endpoint = db.Column(db.String)
    prompt_type = db.Column(db.String)
    response_schema = db.Column(db.String)
    expected_variables = db.Column(db.String)
    input_text = db.Column(db.Text)
    input_audio_url = db.Column(db.String)
    output_text = db.Column(db.Text)
    output_audio_url = db.Column(db.String)
    duration_ms = db.Column(db.Integer)
    tokens_used = db.Column(db.Integer)
    model_version = db.Column(db.String)
    status = db.Column(db.String)
    error = db.Column(db.Text)
    ai_model = db.Column(db.String)
    temperature = db.Column(db.Float)
    top_p = db.Column(db.Float)
    top_k = db.Column(db.Integer)
    max_output_tokens = db.Column(db.Integer)
    step_variables = db.Column(db.String)
    chat_history = db.Column(db.Text)
    
    def to_gemini_request(self):
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