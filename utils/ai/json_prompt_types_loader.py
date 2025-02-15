import json
from typing import Dict, Any, Optional
from pathlib import Path
from .variable_injector import VariableInjector
from .gemini_config import PromptSchema  # Add this import

class ConfigLoader:
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.loaded_configs: Dict[str, PromptSchema] = {}  # Update type hint
        self.variable_injector = VariableInjector()

    def load_config(self, config_name: str, variables: Optional[Dict[str, Any]] = None) -> Optional[PromptSchema]:  # Update return type
        try:
            config_path = self.config_dir / f"{config_name}.json"
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file {config_name}.json not found at {config_path}")

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate required fields
            if not all(key in config for key in ['prompt_text', 'response_schema']):
                raise ValueError(f"Missing required fields in {config_name}.json")

            # Validate schema structure
            if not self._validate_schema_structure(config['response_schema']):
                raise ValueError(f"Invalid schema structure in {config_name}.json")

            # Process variables if provided
            if variables:
                config = self.variable_injector.process_prompt_type(config, variables)  # Use the instance variable

            # Validate and ensure the config matches PromptSchema
            config: PromptSchema = {
                "prompt_text": config["prompt_text"],
                "response_schema": config["response_schema"]
            }

            self.loaded_configs[config_name] = config
            return config

        except json.JSONDecodeError as e:
            print(f"Error decoding {config_name}.json: {str(e)}")
            return None
        except Exception as e:
            print(f"Error loading {config_name}.json: {str(e)}")
            return None

    def _validate_schema_structure(self, schema: Dict[str, Any]) -> bool:
        """Validate the basic structure of a response schema.

        Args:
            schema (Dict[str, Any]): Schema to validate

        Returns:
            bool: True if schema is valid, False otherwise
        """
        required_fields = ['type', 'properties']
        return all(field in schema for field in required_fields)

    def get_loaded_config(self, config_name: str) -> Optional[PromptSchema]:  # Update return type
        return self.loaded_configs.get(config_name)

if __name__ == "__main__":
    # Initialize the config loader
    loader = ConfigLoader('/Users/ebowwa/caringmind/backend/v3/configs')
    
    # Load the default transcription config
    config = loader.load_config('default_transcription')
    
    if config:
        # Validate conversation_analysis in schema
        schema = config['response_schema']
        if 'conversation_analysis' not in schema['properties']:
            print("Error: Missing conversation_analysis in schema properties")
        else:
            print("Successfully loaded default transcription configuration")
            print("\nConfiguration Details:")
            print("=======================")
            print(f"\nPrompt Text:\n{config['prompt_text']}")
            print("\nResponse Schema:")
            print("---------------")
            print(json.dumps(config['response_schema'], indent=2))
    else:
        print("Failed to load default transcription configuration")