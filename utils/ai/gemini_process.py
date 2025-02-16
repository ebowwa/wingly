# backend/route/features/gemini_process_webhook_v2.py
# Updated to support unified batch processing with a single consolidated result

import logging
import re
import json
import os
import datetime
# Add this import to the gemini_config imports
from utils.ai.gemini_config import (
    GeminiPart,
    GeminiInlinePart,
    GeminiContent,
    GeminiRequest,
    PromptSchema,
    GeminiHTTPException  # Add this
)

import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from typing import Dict, List, Union, Any, TypedDict
from dotenv import load_dotenv
from utils.ai.gemini_chat_formatter import _format_chat_messages
from utils.ai.extract_json_from_response import extract_json_from_response
from utils.ai.json_prompt_types_loader import ConfigLoader
from utils.ai.gemini_config import (GeminiPart, GeminiInlinePart,
                                    GeminiContent, GeminiRequest, PromptSchema)

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")
genai.configure(api_key=GOOGLE_API_KEY)

# Path to the configs directory
CONFIGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'configs'
)  # Points to root configs directory

# Initialize the ConfigLoader
config_loader = ConfigLoader(CONFIGS_DIR)

# Update type hint for PROMPTS_SCHEMAS
PROMPTS_SCHEMAS: Dict[str, PromptSchema] = {}
for filename in os.listdir(CONFIGS_DIR):
    if filename.endswith('.json'):
        prompt_type = os.path.splitext(filename)[0]
        config = config_loader.load_config(prompt_type)
        if config:
            PROMPTS_SCHEMAS[prompt_type] = PromptSchema(
                prompt_text=config["prompt_text"],
                response_schema=config["response_schema"])
            logger.info(f"Loaded configuration '{prompt_type}' successfully.")
        else:
            logger.error(f"Failed to load configuration for '{prompt_type}'.")


# Update the function signature
def process_with_gemini(
        uploaded_files: Union[List[GeminiRequest], GeminiRequest],
        prompt_type: str = "default_transcription",
        model_name: str = "gemini-1.5-flash",
        temperature: float = 1.0,
        top_p: float = 0.95,
        top_k: int = 40,
        max_output_tokens: int = 8192,
        step_variables: Dict[str, Any] = None,
        force_json: bool = True) -> Union[Dict[str, Any], str]:
    try:
        config = PROMPTS_SCHEMAS.get(prompt_type)
        if not config:
            logger.error(f"Invalid prompt_type selected: {prompt_type}")
            raise GeminiHTTPException(
                status_code=400, detail=f"Invalid prompt_type: {prompt_type}")

        # Get base prompt and schema from config
        prompt_text = config["prompt_text"]
        response_schema = config["response_schema"] if force_json else None

        # Handle dynamic variable injection if present in the prompt
        variables_to_inject = {}

        # First, get variables from uploaded_files if available
        if isinstance(uploaded_files, object) and hasattr(
                uploaded_files, 'variables'):
            variables_to_inject.update(uploaded_files.variables)

        # Then, override with step-specific variables if provided
        if step_variables:
            variables_to_inject.update(step_variables)

        # Apply variables to prompt and schema
        if variables_to_inject:
            for var_name, var_value in variables_to_inject.items():
                placeholder = f"{{{var_name}}}"
                prompt_text = prompt_text.replace(placeholder, str(var_value))

                if isinstance(response_schema, str):
                    response_schema = response_schema.replace(
                        placeholder, str(var_value))

        # Prepare the prompt and model configuration
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens)

        # Initialize model with generation config
        model = genai.GenerativeModel(model_name=model_name,
                                      generation_config=generation_config)

        logger.info(
            f"Initialized Gemini GenerativeModel with prompt_type '{prompt_type}'"
        )

        # Create dynamic chat history with configurable message sequence
        if isinstance(uploaded_files, list):
            # Handle multiple files with sequential processing
            parts = []
            for file in uploaded_files:
                parts.extend(file["content"]["parts"])
        else:
            # Single file processing
            parts = uploaded_files["content"]["parts"]

        # Create chat history with separate content and prompt messages
        chat_history = [{
            "role": "user",
            "parts": parts
        }, {
            "role": "user",
            "parts": [{
                "text": (f"{prompt_text}\nResponse format: {json.dumps(response_schema, indent=2)}"
                        if force_json else prompt_text)
            }]
        }]

        logger.debug(
            f"Dynamic chat history constructed with {len(parts)} content parts and prompt"
        )

        chat_session = model.start_chat(history=chat_history)
        logger.info("Chat session started with Gemini.")

        # Send a message to the model
        # Handle response based on force_json setting
        response = chat_session.send_message("Process the audio and think deeply")
        logger.debug(f"Received response from Gemini: {response.text}")

        if force_json:
            parsed_result = extract_json_from_response(response.text)
            logger.info("Successfully extracted JSON from Gemini response.")
            return parsed_result
        else:
            return response.text

    except GeminiHTTPException as he:
        logger.error(f"HTTPException in process_with_gemini: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in process_with_gemini: {e}")
        raise GeminiHTTPException(status_code=500,
                                detail="Gemini processing failed")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Test audio file path
    audio_file_path = "audio-samples/Elijah_October_27_2024_9__59PM.ogg"

    # First request without speaker_name
    class ProcessLLMRequestContent:

        def __init__(self, path, include_speaker=False):
            self.path = path
            self.variables = {
                "session_date": "October 27, 2024",
                "session_time": "9:59 PM",
                "file_type": "audio/ogg"
            }

            if include_speaker:
                self.variables["speaker_name"] = "Elijah Cornelius Arbee"

            # Read the audio file as binary
            with open(path, 'rb') as f:
                self.audio_data = f.read()

        def __str__(self):
            return self.path

        def get_parts(self):
            base_text = "Analyzing audio"
            if "speaker_name" in self.variables:
                base_text += f" from {self.variables['speaker_name']}'s session"

            return [{
                "inline_data": {
                    "mime_type": self.variables["file_type"],
                    "data": self.audio_data
                }
            }, {
                "text": base_text
            }]

    try:
        # First request - without speaker name
        print("\n=== First Request (Without Speaker Name) ===")
        test_file_1 = ProcessLLMRequestContent(audio_file_path,
                                               include_speaker=False)
        result_1 = process_with_gemini(uploaded_files={
            "role": "user",
            "content": {
                "parts": test_file_1.get_parts()
            }
        },
                                       prompt_type="default_transcription",
                                       temperature=0.7,
                                       max_output_tokens=4096,
                                       step_variables={
                                           "step_name":
                                           "initial_analysis",
                                           "analysis_type":
                                           "detailed",
                                           "custom_instruction":
                                           "Focus on emotional content"
                                       })

        # Save first result
        output_path_1 = os.path.join(os.path.dirname(audio_file_path),
                                     "analysis_result_no_speaker.json")
        with open(output_path_1, 'w', encoding='utf-8') as f:
            json.dump(result_1, f, indent=2)

        print("\nFirst Processing Result:")
        print(json.dumps(result_1, indent=2))
        print(f"\nFirst result saved to: {output_path_1}")

        # Second request - with speaker name
        print("\n=== Second Request (With Speaker Name) ===")
        test_file_2 = ProcessLLMRequestContent(audio_file_path,
                                               include_speaker=True)
        result_2 = process_with_gemini(uploaded_files={
            "role": "user",
            "content": {
                "parts": test_file_2.get_parts()
            }
        },
                                       prompt_type="default_transcription",
                                       temperature=0.7,
                                       max_output_tokens=4096,
                                       step_variables={
                                           "step_name":
                                           "initial_analysis",
                                           "analysis_type":
                                           "detailed",
                                           "custom_instruction":
                                           "Focus on emotional content"
                                       })

        # Save second result
        output_path_2 = os.path.join(os.path.dirname(audio_file_path),
                                     "analysis_result_with_speaker.json")
        with open(output_path_2, 'w', encoding='utf-8') as f:
            json.dump(result_2, f, indent=2)

        print("\nSecond Processing Result:")
        print(json.dumps(result_2, indent=2))
        print(f"\nSecond result saved to: {output_path_2}")

    except Exception as e:
        print(f"Error during processing: {str(e)}")
