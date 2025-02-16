import asyncio
import google.generativeai as genai  # Changed import
import json
from dotenv import load_dotenv
import os
from typing import Optional, AsyncGenerator, Literal

ResponseType = Literal["TEXT", "AUDIO"]
VoiceName = Literal["Aoede", "Charon", "Fenrir", "Kore", "Puck"]

class GeminiWebSocket:
    def __init__(self, api_key: str, model_id: str = "gemini-pro") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_id)
        
    async def create_session(
        self, 
        response_type: ResponseType = "TEXT", 
        voice_name: Optional[VoiceName] = None
    ) -> genai.GenerativeModel:
        """Initialize a session with specified response type and voice settings"""
        config = {
            "responseModalities": [response_type],
        }
        
        if response_type == "AUDIO" and voice_name:
            config["speechConfig"] = {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name
                    }
                }
            }
        
        return self.model

    async def chat_session(
        self, 
        response_type: ResponseType = "TEXT", 
        voice_name: Optional[VoiceName] = None
    ) -> None:
        """Run an interactive chat session with configurable response type"""
        model = await self.create_session(response_type, voice_name)
        chat = model.start_chat()
        
        print(f"Session started with {response_type} response type")
        if voice_name:
            print(f"Using voice: {voice_name}")
            
        while True:
            message: str = input("User> ")
            if message.lower() in ["exit", "quit"]:
                break
            
            response = await chat.send_message_async(message)
            print(response.text)

if __name__ == "__main__":
    load_dotenv()
    api_key: str = os.getenv('GOOGLE_API_KEY', '')
    gemini: GeminiWebSocket = GeminiWebSocket(api_key)
    
    asyncio.run(gemini.chat_session(response_type="TEXT"))
    
    # For audio response with specific voice
    # Available voices: "Aoede", "Charon", "Fenrir", "Kore", "Puck"
    # asyncio.run(gemini.chat_session(response_type="AUDIO", voice_name="Aoede"))
