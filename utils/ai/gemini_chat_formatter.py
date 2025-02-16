from typing import List, Dict, Any
import datetime
import json
import logging
from pathlib import Path
from jinja2 import Template, meta

# Configure logger
logger = logging.getLogger(__name__)

def _optimize_parts_order(parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Optimize the order of parts according to Gemini's best practices.
    Binary data (images, audio) should be followed by related text prompts.
    """
    binary_parts = []
    text_parts = []
    other_parts = []
    
    for part in parts:
        if "inlineData" in part:
            binary_parts.append(part)
        elif "text" in part:
            text_parts.append(part)
        else:
            other_parts.append(part)
    
    return binary_parts + text_parts + other_parts

def _format_chat_messages(
    messages: List[Dict[str, Any]], 
    variables: Dict[str, str], 
    prompt_type: Dict[str, Any] = None, 
    response_results: List[Dict[str, Any]] = None,
    tool_config: Dict[str, Any] = None,  # Optional: Tool configuration for function calling
    step_variables: Dict[str, Any] = None  # Add step_variables parameter
) -> List[Dict[str, Any]]:
    """
    Format chat messages for the Gemini API, supporting dynamic inputs using Jinja2, multimodal content, and function calling.
    """
    # Merge all variable sources including parameters with step_variables taking precedence
    merged_variables = {
        **variables,
        **({'prompt_text': prompt_type['prompt_text']} if (prompt_type and 'prompt_text' in prompt_type) else {}),
        **(response_results[-1] if response_results else {}),
        **(step_variables if step_variables else {})  # Step variables override previous values
    }
    
    # Find actually used variables in templates
    try:
        used_vars = set()
        for msg in messages:
            if "content" in msg and isinstance(msg["content"], str) and '{{' in msg["content"]:
                template = Template(msg["content"])
                ast = template.environment.parse(msg["content"])
                used_vars.update(v.name for v in meta.find_undeclared_variables(ast))
        
        # Check we have needed variables while allowing extras
        missing = [var for var in used_vars if var not in merged_variables]
        if missing:
            raise ValueError(f"Missing required template variables: {missing}")
            
    except Exception as e:
        print(f"Template validation warning: {str(e)}")
    
    formatted_messages = []
    for msg in messages:
        if "role" not in msg:
            raise ValueError("Message must have a 'role' field")
        
        # Initialize parts list
        parts = []
        
        # Handle text content with Jinja2 templating
        if "content" in msg:
            try:
                # Render all template-enabled fields
                formatted_fields = {}
                for field, value in msg.items():
                    if field == 'role':
                        formatted_fields[field] = value
                        continue
                    if isinstance(value, str) and '{{' in value:
                        template = Template(value)
                        formatted_fields[field] = template.render(**merged_variables)
                        # Special case: Format any string-enclosed JSON in content
                        if field == 'content' and formatted_fields[field].startswith('{'):
                            formatted_fields[field] = json.loads(formatted_fields[field])
                    else:
                        formatted_fields[field] = value
                
                # Handle nested JSON string formatting
                if 'content' in formatted_fields and isinstance(formatted_fields['content'], dict):
                    parts.append({"text": json.dumps(formatted_fields['content'])})
                else:
                    parts.append({"text": str(formatted_fields.get('content', ''))})
                
            except Exception as e:
                raise ValueError(f"Template error in field '{field}': {str(e)}") from e
        
        # Handle audio input with path validation
        if "audio" in msg:
            audio_path = Path(msg["audio"])
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            if audio_path.suffix.lower() not in ['.wav', '.mp3', '.ogg', '.flac', '.m4a']:
                raise ValueError(f"Unsupported audio format: {audio_path.suffix}")
                
            # Read audio file as binary data and encode to base64
            import base64
            with open(audio_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')
                
            parts.append({
                "inlineData": {
                    "mimeType": f"audio/{audio_path.suffix.lower()[1:]}",
                    "data": audio_data
                }
            })
        
        # Handle image input
        if "image" in msg:
            image_path = Path(msg["image"])
            if not image_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            parts.append({
                "inlineData": {
                    "mimeType": f"image/{image_path.suffix.lower()[1:]}",
                    "data": image_data
                }
            })
        
        # Handle PDF input
        if "pdf" in msg:
            parts.append({"pdf": msg["pdf"]})  # Add PDF to parts
        
        # Ensure at least one modality is present
        if not parts:
            raise ValueError("Message must have at least one of 'content', 'audio', 'video', 'image', or 'pdf'")
        
        # Create the formatted message
        formatted_msg = {
            "role": msg["role"],
            "parts": _optimize_parts_order(parts)  # Apply parts optimization
        }
        
        # Add tool configuration if role is 'tool'
        if msg["role"] == "tool" and tool_config:
            formatted_msg["tool"] = tool_config
        
        formatted_messages.append(formatted_msg)
    
    return formatted_messages

# Example usage
if __name__ == "__main__":
    # Define a sample prompt type
    prompt_type = {
        "prompt_text": "Tell me two statements - one truth and one lie about yourself.",
        "response_schema": {
            "truth": "string",
            "lie": "string"
        }
    }
    
    # Sample previous response results
    response_results = [
        {"truth": "I love hiking in the mountains", "lie": "I can speak 10 languages"}
    ]
    
    # Define a tool configuration for function calling
    tool_config = {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g., San Francisco, CA"
                }
            },
            "required": ["location"]
        }
    }
    
    # Define the messages with Jinja2 placeholders and multimodal inputs
    messages = [
        {"role": "user", "content": "Hello {{ name }}! {{ prompt_text }}"},
        {"role": "assistant", "content": "Your previous truth was: '{{ truth }}'. Now, let's continue our conversation."},
        {
            "role": "user",
            "content": "Please analyze this audio.",
            "audio": "audio-samples/Elijah_October_27_2024_9__59PM.ogg"
        },
        {
            "role": "user",
            "content": "And now this image.",
            "image": "caringmind-logo/CircleIcon.png"
        }
    ]
    
    # Define the dynamic variables
    variables = {
        "name": "Alice",
        "day": datetime.datetime.now().strftime("%A, %B %d, %Y")
    }
    
    try:
        # Format the messages with prompt type, previous results, and tool config
        formatted_messages = _format_chat_messages(
            messages=messages,
            variables=variables,
            prompt_type=prompt_type,
            response_results=response_results,
            tool_config=tool_config
        )
        print("Formatted messages:", json.dumps(formatted_messages, indent=2))
    except Exception as e:
        print(f"Error formatting messages: {e}")
