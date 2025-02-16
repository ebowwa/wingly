import asyncio
from google import genai
import json

class GeminiWebSocket:
    def __init__(self, api_key, model_id="gemini-2.0-flash-exp"):
        self.client = genai.Client(
            api_key=api_key, 
            http_options={'api_version': 'v1alpha'}
        )
        self.model_id = model_id
        
    async def create_session(self, response_type="TEXT", voice_name=None):
        """Initialize a session with specified response type and voice settings"""
        config = {
            "responseModalities": [response_type],
        }
        
        # Add voice configuration if specified
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

    async def chat_session(self, response_type="TEXT", voice_name=None):
        """Run an interactive chat session with configurable response type"""
        async with await self.create_session(response_type, voice_name) as session:
            print(f"Session started with {response_type} response type")
            if voice_name:
                print(f"Using voice: {voice_name}")
                
            while True:
                message = input("User> ")
                if message.lower() in ["exit", "quit"]:
                    break
                
                # Send message with turn completion indicator
                await session.send(input=message, end_of_turn=True)
                
                # Process response based on type
                async for response in session.receive():
                    if response_type == "TEXT":
                        if response.text:
                            print(response.text, end="")
                    elif response_type == "AUDIO":
                        # Handle audio response
                        if hasattr(response, 'audio'):
                            # Process audio data
                            print("Audio response received")
                    
                    # Handle interruptions
                    if hasattr(response, 'interrupted') and response.interrupted:
                        print("\nResponse interrupted by user")
                        break

async def main():
    # Example usage
    api_key = "YOUR_GEMINI_API_KEY"
    gemini = GeminiWebSocket(api_key)
    
    # For text response
    await gemini.chat_session(response_type="TEXT")
    
    # For audio response with specific voice
    # Available voices: "Aoede", "Charon", "Fenrir", "Kore", "Puck"
    # await gemini.chat_session(response_type="AUDIO", voice_name="Aoede")

if __name__ == "__main__":
    asyncio.run(main())