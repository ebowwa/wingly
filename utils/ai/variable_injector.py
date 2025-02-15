from typing import Dict, Any, List, Optional
from jinja2 import Template, meta, Environment, StrictUndefined
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Set logging level to INFO

class VariableInjector:
    def __init__(self):
        # Create Jinja2 environment with strict undefined variable handling
        self.env = Environment(undefined=StrictUndefined)
    
    def validate_template_variables(self, template_str: str, variables: Dict[str, Any]) -> List[str]:
        """Validate that all required variables are present in the variables dict.
        
        Args:
            template_str: String containing Jinja2 template
            variables: Dictionary of variables to validate
            
        Returns:
            List of missing variable names
        """
        try:
            template = self.env.parse(template_str)
            required_vars = meta.find_undeclared_variables(template)
            logger.info(f"Required variables in template: {required_vars}")
            logger.info(f"Provided variables: {variables}")
            return [var for var in required_vars if var not in variables]
        except Exception as e:
            logger.error(f"Template validation error: {str(e)}")
            raise ValueError(f"Template validation failed: {str(e)}")
    
    def inject_variables(self, content: Any, variables: Dict[str, Any]) -> Any:
        """Recursively inject variables into content, handling nested structures.
        
        Args:
            content: Content to inject variables into (string, dict, or list)
            variables: Variables to inject
            
        Returns:
            Content with variables injected
        """
        logger.info(f"Injecting variables into content: {content}")
        logger.info(f"Using variables: {variables}")
        
        if isinstance(content, str) and '{{' in content:
            try:
                template = Template(content)
                rendered = template.render(**variables)
                logger.info(f"Rendered content: {rendered}")
                
                # Handle JSON string content
                if rendered.strip().startswith('{') and rendered.strip().endswith('}'): 
                    try:
                        parsed_json = json.loads(rendered)
                        logger.info(f"Parsed JSON from rendered content: {parsed_json}")
                        return parsed_json
                    except json.JSONDecodeError:
                        return rendered
                return rendered
            except Exception as e:
                logger.error(f"Variable injection error: {str(e)}")
                raise ValueError(f"Failed to inject variables: {str(e)}")
        elif isinstance(content, dict):
            return {k: self.inject_variables(v, variables) for k, v in content.items()}
        elif isinstance(content, list):
            return [self.inject_variables(item, variables) for item in content]
        return content
    
    def process_chat_history(self, 
        messages: List[Dict[str, Any]], 
        variables: Dict[str, Any],
        prompt_type: Optional[Dict[str, Any]] = None,
        response_results: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Process chat history messages with variable injection.
        
        Args:
            messages: List of chat messages
            variables: Variables to inject
            prompt_type: Optional prompt type configuration
            response_results: Optional previous response results
            
        Returns:
            Processed messages with variables injected
        """
        # Merge variables from all sources
        merged_variables = {
            **variables,
            **({'prompt_text': prompt_type['prompt_text']} if prompt_type and 'prompt_text' in prompt_type else {}),
            **(response_results[-1] if response_results else {})
        }
        
        logger.info(f"Merged variables for chat history processing: {merged_variables}")
        
        # Validate all templates first
        for msg in messages:
            if 'content' in msg and isinstance(msg['content'], str):
                missing = self.validate_template_variables(msg['content'], merged_variables)
                if missing:
                    raise ValueError(f"Missing required variables: {missing}")
        
        # Process messages with validated variables
        return [self.inject_variables(msg, merged_variables) for msg in messages]
    
    def process_prompt_type(self, prompt_type: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Process prompt type configuration with variable injection.
        
        Args:
            prompt_type: Prompt type configuration
            variables: Variables to inject
            
        Returns:
            Processed prompt type with variables injected
        """
        if not isinstance(prompt_type, dict):
            raise ValueError("prompt_type must be a dictionary")
            
        logger.info(f"Processing prompt type with variables: {variables}")
        
        # Validate prompt text template if present
        if 'prompt_text' in prompt_type and isinstance(prompt_type['prompt_text'], str):
            missing = self.validate_template_variables(prompt_type['prompt_text'], variables)
            if missing:
                raise ValueError(f"Missing required variables in prompt_text: {missing}")
        
        return self.inject_variables(prompt_type, variables)
# Example usage
if __name__ == "__main__":
    import os
    import requests
    from pathlib import Path
   