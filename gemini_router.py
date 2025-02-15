# backend/route/gemini/gemini_audio_handling_noauth.py

# Stateless API Design no persistence!
# audio handling
# client - manage the file urls to send included in the requests.. to manage chats/longer context
# GEMINI RULES: Each project can store up to 20GB of files, 
# with each individual file not exceeding 2GB in size, 
# Prompt Constraints: While there's no explicit limit on the number of audio files in a single prompt, 
# the combined length of all audio files in a prompt must not exceed 9.5 hours.
import os
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Tuple, Union
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import traceback
from tenacity import retry, stop_after_attempt, wait_exponential
from functools import partial
# from services.gemini_process import process_with_gemini
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
# Load environment variables
load_dotenv()

# Initialize FastAPI router with tags and prefix
router = APIRouter(
    tags=["gemini"],
    responses={404: {"description": "Not found"}},
)

# Configure Gemini API
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    logger.critical("GOOGLE_API_KEY not found in environment variables.")
    raise EnvironmentError("GOOGLE_API_KEY not found in environment variables.")

genai.configure(api_key=google_api_key)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def upload_to_gemini(file_content: bytes, mime_type: Optional[str] = None) -> object:
    """
    Prepares file content for Gemini by encoding it as base64.
    """
    try:
        import base64
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        return {
            "mime_type": mime_type or "audio/ogg",
            "data": encoded_content
        }
    except Exception as e:
        logger.error(f"Unexpected error preparing file: {e}")
        traceback.print_exc()
        raise

def process_audio_with_gemini(
    filename: str,
    uploaded_file: object,
    prompt_type: str,
    model_name: str,
    temperature: float,
    top_p: float,
    top_k: int,
    max_output_tokens: int
) -> Union[Tuple[str, object], Exception]:
    try:
        logger.debug(f"Processing with Gemini webhook for file: {filename}")
        
        # Format the file data for Gemini
        formatted_data = {
            "role": "user",
            "content": {
                "parts": [
                    {
                        "inline_data": uploaded_file  # Use the uploaded file data directly
                    }
                ]
            }
        }
        
        gemini_result = process_with_gemini(
            formatted_data,
            prompt_type=prompt_type,
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens
        )
        logger.debug(f"Gemini processing successful for file: {filename}")
        return (filename, gemini_result)
    except Exception as e:
        logger.error(f"Error in Gemini processing for file {filename}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini processing failed: {str(e)}")

@router.post("/process-audio")
async def process_audio(
    files: List[UploadFile] = File(...),
    prompt_type: str = Query(..., description="Type of prompt and schema to use"),
    batch: bool = Query(False, description="Process files in batch if True"),
    model_name: str = Query(default="gemini-1.5-flash", description="Name of the Gemini model to use"),
    temperature: float = Query(1.0, description="Temperature parameter for generation"),
    top_p: float = Query(0.95, description="Top-p parameter for generation"),
    top_k: int = Query(40, description="Top-k parameter for generation"),
    max_output_tokens: int = Query(8192, description="Maximum output tokens")
):
    """
    Process multiple audio files concurrently with improved error handling.
    Allows specifying the Gemini model and generation parameters.
    """
    supported_mime_types = {
        "audio/wav", "audio/mp3", "audio/aiff",
        "audio/aac", "audio/ogg", "audio/flac"
    }

    if not files:
        logger.warning("No files uploaded in the request.")
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # Validate all files
    for file in files:
        if file.content_type not in supported_mime_types:
            logger.warning(f"Unsupported file type: {file.content_type} for file {file.filename}.")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {supported_mime_types}"
            )

    try:
        # Process files concurrently for uploading
        processing_tasks = [async_upload_file_to_gemini(file) for file in files]
        uploaded_files = await asyncio.gather(*processing_tasks, return_exceptions=True)

        # Check for any exceptions in uploaded_files
        errors = []
        valid_uploaded_files = []
        for file, uploaded_file in zip(files, uploaded_files):
            if isinstance(uploaded_file, Exception):
                logger.error(f"Error processing file {file.filename}: {uploaded_file}")
                errors.append({
                    "file": file.filename,
                    "status": "failed",
                    "error": str(uploaded_file)
                })
            else:
                valid_uploaded_files.append((file.filename, uploaded_file))

        if not valid_uploaded_files:
            logger.warning("All file uploads failed.")
            return JSONResponse(content={"results": errors})

        results = errors.copy()

        if batch:
            # Process with Gemini webhook with batch=True
            try:
                logger.debug("Starting batch processing with Gemini webhook.")
                gemini_result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    partial(
                        process_with_gemini,
                        [uploaded_file for _, uploaded_file in valid_uploaded_files],
                        prompt_type=prompt_type,
                        batch=True,
                        model_name=model_name,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        max_output_tokens=max_output_tokens
                    )
                )
                results.append({
                    "files": [filename for filename, _ in valid_uploaded_files],
                    "status": "processed",
                    "data": gemini_result
                })
                logger.debug("Batch processing with Gemini webhook successful.")
            except Exception as e:
                logger.error(f"Error in Gemini processing (batch): {e}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail="Gemini processing failed.")
        else:
            # Process each file individually
            processing_tasks = []
            for filename, uploaded_file in valid_uploaded_files:
                task = asyncio.get_event_loop().run_in_executor(
                    None,
                    partial(
                        process_audio_with_gemini,
                        filename,
                        uploaded_file,
                        prompt_type,
                        model_name,
                        temperature,
                        top_p,
                        top_k,
                        max_output_tokens
                    )
                )
                processing_tasks.append(task)

            individual_results = await asyncio.gather(*processing_tasks, return_exceptions=True)

            for original_file, result in zip(valid_uploaded_files, individual_results):
                filename, _ = original_file
                if isinstance(result, Exception):
                    logger.error(f"Error in Gemini processing for file {filename}: {result}")
                    results.append({
                        "file": filename,
                        "status": "failed",
                        "error": str(result)
                    })
                elif isinstance(result, tuple):
                    fname, gemini_result = result
                    results.append({
                        "file": fname,
                        "status": "processed",
                        "data": gemini_result
                    })
                else:
                    logger.error(f"Unexpected result type for file {filename}: {result}")
                    results.append({
                        "file": filename,
                        "status": "failed",
                        "error": "Unexpected processing result."
                    })

        return JSONResponse(content={"results": results})

    except Exception as e:
        logger.error(f"Unexpected error in process_audio: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error. Please check the server logs."
        )


@router.post("/start-conversation")
async def start_conversation():
    """
    Start a conversation with the Gemini model.
    
    Ask the user for defined input and generate a summary
    """
    questions = [
        "Introduce yourself to your prospective partner",
        "What are you looking for in a partner",
        "What is your relationship vision."
    ]

    answers = []
    
    for question in questions:
        await asyncio.sleep(0.5)  # Allow time for user to read question
        user_input = input(f"{question}\n")
        answers.append(user_input)
        # Process user input (e.g., store it, send it to the Gemini model)
        # ...

    """
    generate a summary of the conversation
    """

    summary = "Here is a summary of the conversation."
    return summary




# Export the router at the bottom
gemini_router = router