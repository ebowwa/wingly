from fastapi import APIRouter, UploadFile, File, HTTPException, Query, FastAPI, WebSocket, WebSocketDisconnect, Request
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Initialize the router
router = APIRouter()

# Load environment variables
load_dotenv()

# Initialize FastAPI router with tags and prefix
router = APIRouter(
    tags=["websocket"],
    responses={404: {"description": "Not found"}},
)

# Initialize FastAPI app
app = FastAPI()

# Configure Gemini API
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    logger.critical("GOOGLE_API_KEY not found in environment variables.")
    raise EnvironmentError("GOOGLE_API_KEY not found in environment variables.")

genai.configure(api_key=google_api_key)


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
    """Handles an interactive conversation via WebSockets."""
    try:
        await websocket.accept()
        answers = []

        try:
            for question in questions:
                logging.info(f"Sending question: {question}")
                await websocket.send_text(question)  # Ask the question
                logging.info("Waiting for user response...")
                user_response = await websocket.receive_text()  # Wait for user reply
                logging.info(f"Received response: {user_response}")
                answers.append(user_response)  # Store the answer

            # Generate the final summary
            summary = {
                "Summary": {
                    "Introduction": answers[0],
                    "Looking for": answers[1],
                    "Vision": answers[2]
                }
            }
            logging.info("Sending summary")
            await websocket.send_text(json.dumps(summary, indent=2))  # Send summary

        except WebSocketDisconnect:
            logging.info("User disconnected")
        except Exception as e:
            logging.error(f"Error in websocket communication: {str(e)}")
            raise
    except Exception as e:
        logging.error(f"Error accepting websocket connection: {str(e)}")
        raise


socket_router = router