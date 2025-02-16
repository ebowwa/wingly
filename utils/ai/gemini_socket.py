import asyncio
import google.generativeai as genai  # Changed import
import json
from dotenv import load_dotenv
import os
from typing import Optional, AsyncGenerator, Literal, Dict, Any, List, Union

ResponseType = Literal["TEXT", "AUDIO"]
VoiceName = Literal["Aoede", "Charon", "Fenrir", "Kore", "Puck"]

class ServerMessage:
    def __init__(self, message_type: str, content: Dict[str, Any]):
        self.message_type = message_type
        self.content = content

class GeminiWebSocket:
    def __init__(self, api_key: str, model_id: str = "gemini-2.0-flash-exp") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_id)
        self.tools: List[Dict[str, Any]] = []
        self.active_function_calls: Dict[str, Any] = {}
        
    def add_tool(self, tool: Dict[str, Any]) -> None:
        """Add a tool (function) that the model can use"""
        self.tools.append(tool)

    async def handle_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Handle function calls from the model"""
        function_id = tool_call.get('id')
        function_name = tool_call.get('name')
        function_args = tool_call.get('args', {})
        
        # Store active function call
        self.active_function_calls[function_id] = {
            'name': function_name,
            'args': function_args,
            'status': 'pending'
        }
        
        # Here you would implement the actual function execution
        # For now, we'll just return a dummy response
        return {
            'id': function_id,
            'response': f"Executed {function_name} with args {function_args}"
        }

    async def create_session(
        self, 
        response_type: ResponseType = "TEXT", 
        voice_name: Optional[VoiceName] = None
    ) -> genai.GenerativeModel:
        """Initialize a session with specified response type and voice settings"""
        config = {
            "responseModalities": [response_type],
            "tools": self.tools
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

    async def process_server_message(self, message: Any) -> ServerMessage:
        """Process different types of server messages"""
        if hasattr(message, 'tool_calls'):
            return ServerMessage("BidiGenerateContentToolCall", {
                'tool_calls': message.tool_calls
            })
        elif hasattr(message, 'text'):
            return ServerMessage("BidiGenerateContentServerContent", {
                'text': message.text
            })
        elif hasattr(message, 'interrupted'):
            return ServerMessage("BidiGenerateContentToolCallCancellation", {
                'interrupted': True,
                'cancelled_ids': [call_id for call_id in self.active_function_calls]
            })
        return None

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
            server_message = await self.process_server_message(response)
            
            if server_message:
                if server_message.message_type == "BidiGenerateContentToolCall":
                    for tool_call in server_message.content['tool_calls']:
                        result = await self.handle_tool_call(tool_call)
                        # Send tool response back to the model
                        response = await chat.send_message_async(json.dumps(result))
                
                elif server_message.message_type == "BidiGenerateContentServerContent":
                    print(server_message.content['text'])
                
                elif server_message.message_type == "BidiGenerateContentToolCallCancellation":
                    print("\nFunction calls cancelled due to interruption")
                    self.active_function_calls.clear()

if __name__ == "__main__":
    load_dotenv()
    api_key: str = os.getenv('GOOGLE_API_KEY', '')
    gemini = GeminiWebSocket(api_key)
    
    # Example tool definition
    gemini.add_tool({
        "name": "get_weather",
        "description": "Get the weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    })
    
    asyncio.run(gemini.chat_session(response_type="TEXT"))
    
    # For audio response with specific voice
    # Available voices: "Aoede", "Charon", "Fenrir", "Kore", "Puck"
    # asyncio.run(gemini.chat_session(response_type="AUDIO", voice_name="Aoede"))
