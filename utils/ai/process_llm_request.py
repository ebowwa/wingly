import os
import json
import base64
from typing import Dict, Any, List
from datetime import datetime

class ProcessLLMRequestContent:
    def __init__(self, path: str, variables: Dict[str, Any] = None):
        """
        Initialize a ProcessLLMRequestContent instance.
        
        Args:
            path: Path to the audio file
            variables: Dictionary of variables to be used in processing
        """
        self.path = path
        self.variables = variables or {}
        
        # Determine file type from the file extension
        self.variables["file_type"] = f"audio/{os.path.splitext(path)[1][1:]}"
        
        # Read the audio file as binary and encode as base64
        with open(path, 'rb') as f:
            self.audio_data = base64.b64encode(f.read()).decode('utf-8')

    def get_parts(self) -> List[Dict]:
        """
        Generate the parts structure required by Gemini API.
        """
        base_text = "Analyzing audio"
        if "speaker_name" in self.variables:
            base_text += f" from {self.variables['speaker_name']}'s session"

        return [{
            "inline_data": {
                "mime_type": self.variables["file_type"],
                "data": self.audio_data  # Now using base64 encoded data
            }
        }, {
            "text": base_text
        }]

    def to_gemini_request(self) -> Dict:
        """
        Convert to the format expected by process_with_gemini.
        """
        return {
            "role": "user",
            "content": {
                "parts": self.get_parts()
            }
        }

if __name__ == "__main__":
    # Example usage
    audio_path = "audio-samples/Elijah_October_27_2024_9__59PM.ogg"
    
    # Example 1: Basic usage without speaker
    basic_request = ProcessLLMRequestContent(
        path=audio_path,
        variables={
            "session_date": datetime.now().strftime("%B %d, %Y"),
            "session_time": datetime.now().strftime("%I:%M %p")
        }
    )
    print("\n=== Basic Request ===")
    print(json.dumps(basic_request.to_gemini_request(), indent=2))

    # Example 2: Usage with speaker information
    speaker_request = ProcessLLMRequestContent(
        path=audio_path,
        variables={
            "session_date": datetime.now().strftime("%B %d, %Y"),
            "session_time": datetime.now().strftime("%I:%M %p"),
            "speaker_name": "Elijah Cornelius Arbee"
        }
    )
    print("\n=== Request with Speaker ===")
    print(json.dumps(speaker_request.to_gemini_request(), indent=2))