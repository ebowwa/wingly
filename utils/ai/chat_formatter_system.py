from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.ai.variable_injector import VariableInjector
from utils.ai.json_prompt_types_loader import ConfigLoader
from utils.ai.gemini_chat_formatter import _format_chat_messages
import logging

logger = logging.getLogger(__name__)

class ChatFormatterSystem:
    def __init__(self, config_dir: str):
        """Initialize the chat formatter system.
        
        Args:
            config_dir: Directory containing prompt type configuration files
        """
        self.config_loader = ConfigLoader(config_dir)
        self.variable_injector = VariableInjector()
        
    def format_chat(self,
        messages: List[Dict[str, Any]],
        variables: Dict[str, Any],
        prompt_type_name: Optional[str] = None,
        response_results: Optional[List[Dict[str, Any]]] = None,
        tool_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format chat messages with all necessary processing.
        
        Args:
            messages: List of chat messages to format
            variables: Variables to inject into templates
            prompt_type_name: Name of prompt type configuration to load (without .json extension)
            response_results: Optional previous response results
            tool_config: Optional tool configuration for function calling
            
        Returns:
            Formatted messages ready for the Gemini API
        """
        try:
            # Load prompt type configuration if specified
            prompt_type = None
            if prompt_type_name:
                prompt_type = self.config_loader.load_config(prompt_type_name, variables)
                if not prompt_type:
                    logger.error(f"Failed to load prompt type: {prompt_type_name}")
                    raise ValueError(f"Failed to load prompt type: {prompt_type_name}")
            
            # Format messages using the Gemini formatter
            formatted_messages = _format_chat_messages(
                messages=messages,
                variables=variables,
                prompt_type=prompt_type,
                response_results=response_results,
                tool_config=tool_config
            )
            
            return formatted_messages
            
        except Exception as e:
            logger.error(f"Error in chat formatting: {str(e)}")
            raise

if __name__ == "__main__":
    # Example usage
    import datetime
    
    # Initialize the system
    formatter = ChatFormatterSystem('backend/v3/configs')
    
    # Example messages
    messages = [
        {"role": "user", "content": "Hello {{ name }}! {{ prompt_text }}"},
        {"role": "assistant", "content": "Your previous truth was: '{{ truth }}'. Now, let's continue our conversation."},
        {"role": "user", "content": "Please analyze this audio.", "audio": "audio-samples/Elijah_October_27_2024_9__59PM.ogg"},
    ]
    
    # Example variables
    variables = {
        "name": "Alice",
        "day": datetime.datetime.now().strftime("%A, %B %d, %Y"),
        "name_analysis": "Speaker demonstrates clear articulation with moderate confidence...",  # Add name_analysis
        "step_name": "initial_analysis",
        "analysis_type": "detailed",
        "custom_instruction": "Focus on emotional content"
    }
    
    # Example tool configuration
    tool_config = {
        "function_declarations": [
            {
                "name": "get_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city and state, e.g., San Francisco, CA"}
                    },
                    "required": ["location"]
                }
            }
        ]
    }
    
    try:
        # Format chat with a specific prompt type
        formatted_chat = formatter.format_chat(
            messages=messages,
            variables=variables,  # Use variables directly since it already includes step variables
            prompt_type_name="truthnlie",
            tool_config=tool_config
        )
        print("Formatted chat messages:")
        print(formatted_chat)
        
    except Exception as e:
        print(f"Error: {str(e)}")