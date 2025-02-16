from fastapi import APIRouter, UploadFile, File, HTTPException, Query, FastAPI, WebSocket, WebSocketDisconnect, Request
from dotenv import load_dotenv
import os
import google.generativeai as genai
import logging
import json
from typing import Optional, Dict, Any
from utils.ai.gemini_socket import GeminiWebSocket

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the router
router = APIRouter(
    tags=["websocket"],
    responses={404: {"description": "Not found"}},
)

# Load environment variables
load_dotenv()

# Configure Gemini API
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    logger.critical("GOOGLE_API_KEY not found in environment variables.")
    raise EnvironmentError("GOOGLE_API_KEY not found in environment variables.")

# Initialize GeminiWebSocket
gemini_socket = GeminiWebSocket(api_key=google_api_key)

# Add tools
gemini_socket.add_tool({
    "name": "get_relationship_profile",
    "description": "Generate a relationship profile based on user responses",
    "parameters": {
        "type": "object",
        "properties": {
            "introduction": {"type": "string"},
            "looking_for": {"type": "string"},
            "vision": {"type": "string"}
        },
        "required": ["introduction", "looking_for", "vision"]
    }
})

questions = [
    "Introduce yourself to your prospective partner.",
    "What are you looking for in a partner?",
    "What is your relationship vision?"
]

@router.get("/")
async def healthcheck():
    return {"status": "ok"}

@router.websocket("/conversation")
async def conversation_endpoint(websocket: WebSocket):
    """Handles an interactive conversation via WebSockets using Gemini."""
    try:
        await websocket.accept()
        answers = []
        
        # Initialize Gemini chat session
        chat = await gemini_socket.create_session(response_type="TEXT")
        
        try:
            for question in questions:
                logging.info(f"Sending question: {question}")
                await websocket.send_text(question)
                
                user_response = await websocket.receive_text()
                logging.info(f"Received response: {user_response}")
                answers.append(user_response)
                
                # Process response through Gemini
                response = await chat.send_message_async(
                    f"User's response to '{question}': {user_response}"
                )
                
                # Send Gemini's analysis back to the user
                if hasattr(response, 'text'):
                    await websocket.send_text(response.text)

            # Generate final summary using Gemini's tool
            profile_data = {
                "introduction": answers[0],
                "looking_for": answers[1],
                "vision": answers[2]
            }
            
            final_response = await chat.send_message_async(
                f"Please analyze this relationship profile and provide insights: {json.dumps(profile_data)}"
            )
            
            await websocket.send_text(json.dumps({
                "Summary": profile_data,
                "Analysis": final_response.text if hasattr(final_response, 'text') else "No analysis available"
            }, indent=2))

        except WebSocketDisconnect:
            logging.info("User disconnected")
        except Exception as e:
            logging.error(f"Error in websocket communication: {str(e)}")
            await websocket.send_text(f"Error: {str(e)}")
            
    except Exception as e:
        logging.error(f"Error accepting websocket connection: {str(e)}")
        raise

socket_router = router