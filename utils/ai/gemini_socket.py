import asyncio
from google import genai
import json
from dotenv import load_dotenv
import os
from typing import Optional, AsyncGenerator, Literal

ResponseType = Literal["TEXT", "AUDIO"]
VoiceName = Literal["Aoede", "Charon", "Fenrir", "Kore", "Puck"]

class GeminiWebSocket:
    def __init__(self, api_key: str, model_id: str = "gemini-2.0-flash-exp") -> None:
        self.client: genai.Client = genai.Client(
            api_key=api_key, 
            http_options={'api_version': 'v1alpha'}
        )
        self.model_id: str = model_id
        
    async def create_session(
        self, 
        response_type: ResponseType = "TEXT", 
        voice_name: Optional[VoiceName] = None
    ) -> genai.live.Session:
        """Initialize a session with specified response type and voice settings"""
        config: dict[str, list[str] | dict] = {
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
        
        return await self.client.aio.live.connect(
            model=self.model_id,
            config=config
        )

    async def chat_session(
        self, 
        response_type: ResponseType = "TEXT", 
        voice_name: Optional[VoiceName] = None
    ) -> None:
        """Run an interactive chat session with configurable response type"""
        async with await self.create_session(response_type, voice_name) as session:
            print(f"Session started with {response_type} response type")
            if voice_name:
                print(f"Using voice: {voice_name}")
                
            while True:
                message: str = input("User> ")
                if message.lower() in ["exit", "quit"]:
                    break
                
                await session.send(input=message, end_of_turn=True)
                
                async for response in session.receive():
                    if response_type == "TEXT":
                        if response.text:
                            print(response.text, end="")
                    elif response_type == "AUDIO":
                        if hasattr(response, 'audio'):
                            print("Audio response received")
                    
                    if hasattr(response, 'interrupted') and response.interrupted:
                        print("\nResponse interrupted by user")
                        break

if __name__ == "__main__":
    load_dotenv()
    api_key: str = os.getenv('GOOGLE_API_KEY', '')
    gemini: GeminiWebSocket = GeminiWebSocket(api_key)
    
    asyncio.run(gemini.chat_session(response_type="TEXT"))
    
    # For audio response with specific voice
    # Available voices: "Aoede", "Charon", "Fenrir", "Kore", "Puck"
    # asyncio.run(gemini.chat_session(response_type="AUDIO", voice_name="Aoede"))
