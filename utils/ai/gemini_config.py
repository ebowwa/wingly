from typing import Dict, List, Union, TypedDict

class GeminiHTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")

class PromptSchema(TypedDict):
    prompt_text: str
    response_schema: Union[str, dict]

class GeminiPart(TypedDict):
    text: str

class GeminiInlinePart(TypedDict):
    inline_data: Dict[str, Union[str, bytes]]

class GeminiContent(TypedDict):
    parts: List[Union[GeminiPart, GeminiInlinePart]]

class GeminiRequest(TypedDict):
    role: str
    content: GeminiContent

def get_generation_config(
    temperature: float = 1.0,
    top_p: float = 0.95,
    top_k: int = 40,
    max_output_tokens: int = 8192,
    response_schema: Dict = None,
    response_mime_type: str = "application/json"
) -> Dict:
    """Generate configuration settings for Gemini model.
    
    Args:
        temperature: Controls randomness in the output. Higher values make the output more random.
        top_p: Nucleus sampling parameter. Lower values make the output more focused.
        top_k: Number of highest probability vocabulary tokens to keep for top-k filtering.
        max_output_tokens: Maximum number of tokens to generate.
        response_schema: Schema defining the expected response structure.
        response_mime_type: MIME type of the expected response.
    
    Returns:
        Dict containing the generation configuration settings.
    """
    return {
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_output_tokens": max_output_tokens,
        "response_schema": response_schema,
        "response_mime_type": response_mime_type,
    }