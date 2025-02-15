# prompt_type System

## Overview
This directory contains prompt configurations for the Gemini API integration. Each configuration defines a specific type of analysis or interaction with the audio input.

## Structure
Each prompt configuration is a standalone JSON file with a simple, standardized structure:

```json
{
    "prompt_text": "The actual prompt instructions",
    "response_schema": {
        "type": "object",
        "properties": {
            // Expected response fields
        }
    }
}
```

## Key Components

1. **Filename = Prompt Type**
   - The JSON filename serves as the prompt type identifier
   - Example: `name_input.json` → prompt_type = "name_input"

2. **Prompt Text**
   - Clear instructions for the Gemini model
   - Can include context, steps, and specific requirements
   - Should be focused on a single type of analysis

3. **Response Schema**
   - Defines the expected structure of the Gemini response
   - Uses standard JSON Schema format
   - Must include `type` and `properties`

## Adding New Configurations

1. Create a new JSON file with a descriptive name
2. Include both `prompt_text` and `response_schema`
3. Place in appropriate subdirectory (audio/, text/, multi-modality/)
4. Ensure schema matches expected response format

Example:
```json
{
    "prompt_text": "Analyze this audio for...",
    "response_schema": {
        "type": "object",
        "properties": {
            "field1": {
                "type": "string",
                "description": "Description of field1"
            }
        }
    }
}
```

## Best Practices

1. **Prompt Text**
   - Be specific and clear
   - Break complex tasks into steps
   - Include validation requirements
   - Prevent hallucination with explicit instructions

2. **Response Schema**
   - Keep it simple and focused
   - Include descriptions for all fields
   - Use appropriate data types
   - Define required fields when necessary

3. **Organization**
   - Use descriptive filenames
   - Group related configs in subdirectories
   - Keep schemas consistent across similar analyses

## System Integration

The configurations are automatically loaded by:
- `PromptHandler`: Loads and validates configs
- `ResponseHandler`: Validates responses against schemas
- `Core`: Processes with Gemini API

## Example Configurations

1. **Name Input Analysis** (`name_input.json`)
   - Analyzes name pronunciation and identity
   - Includes prosody and psychological analysis

2. **Default Transcription** (`default_transcription.json`)
   - Basic audio transcription
   - Includes speaker identification and tone analysis

3. **Truth or Lie Game** (`truthnlie.json`)
   - Game-based psychological analysis
   - Includes deception detection

## Validation

Responses are validated against schemas by the ResponseHandler:
```python
if self.validate_response(json_response):
    if "name" in json_response:  # name_input schema
        return json_response
    return {**self.default_schema, "transcription": json.dumps(json_response)}
```

## Scaling

The system is designed to scale by:
1. Adding new JSON config files
2. Following the standard structure
3. Letting the existing handlers manage validation and processing

No code changes needed for new configs unless adding entirely new types of analysis.
