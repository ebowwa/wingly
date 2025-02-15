"""Token Counter Module for Gemini API"""

import logging
from typing import Union, List, Dict, Any, Optional
import google.generativeai as genai
from PIL import Image
from pathlib import Path
import wave
import io
import os
import tempfile
import subprocess
import sys
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

# Configure Rich console and logging
console = Console(force_terminal=True)

# Custom formatter to keep debug messages concise
class ConciseFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.DEBUG:
            # For debug messages, just show the message without the level name
            return record.getMessage()
        # For other levels, use standard formatting
        return super().format(record)

# Configure logging with custom handler
handler = RichHandler(
    console=console,
    rich_tracebacks=True,
    show_time=False,
    show_path=False,  # Don't show file path
    enable_link_path=False  # Don't show clickable links
    # add requests and responses to this 
)
handler.setFormatter(ConciseFormatter("%(message)s"))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler]
)

logger = logging.getLogger(__name__)

class TokenCounter:
    """Utility class for counting tokens in various content types for Gemini API."""
    
    # Token constants
    IMAGE_TOKENS = 258
    VIDEO_TOKENS_PER_SECOND = 263
    AUDIO_TOKENS_PER_SECOND = 32
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model_name)
        self.console = console
        logger.info(f"TokenCounter initialized with model: {model_name}")

    def _inspect_audio_content(self, audio_content: bytes) -> None:
        """Debug helper to inspect audio content."""
        try:
            # Check first few bytes for WAV header
            if len(audio_content) > 12:
                header = audio_content[:12]
                logger.debug(f"Audio header bytes: {header.hex()}")
                if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
                    logger.debug("Valid WAV header detected")
                else:
                    logger.warning("Invalid or non-WAV header detected")
            
            logger.debug(f"Audio content size: {len(audio_content)} bytes")
        except Exception as e:
            logger.error(f"Error inspecting audio content: {e}")

    def _normalize_audio_content(self, audio_content: bytes) -> Optional[bytes]:
        """Normalize audio content to ensure it's valid WAV format."""
        try:
            # First try to read as WAV
            with io.BytesIO(audio_content) as buf:
                try:
                    with wave.open(buf, 'rb') as wav:
                        # If we can open it as WAV, it's already good
                        return audio_content
                except wave.Error:
                    logger.debug("Content is not in WAV format, attempting conversion")
                    
            # If not WAV, try converting using ffmpeg
            with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as temp_in:
                temp_in.write(audio_content)
                temp_in_path = temp_in.name
                
            temp_out_path = temp_in_path + '.wav'
            
            try:
                cmd = [
                    'ffmpeg',
                    '-i', temp_in_path,
                    '-acodec', 'pcm_s16le',  # Convert to 16-bit PCM WAV
                    '-ar', '44100',  # Standard sample rate
                    '-ac', '1',  # Mono
                    '-y',  # Overwrite output
                    temp_out_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    with open(temp_out_path, 'rb') as f:
                        normalized_content = f.read()
                    logger.debug("Successfully normalized audio to WAV format")
                    return normalized_content
                else:
                    logger.error(f"FFmpeg conversion failed: {result.stderr}")
                    return None
            finally:
                # Clean up temp files
                try:
                    os.unlink(temp_in_path)
                    if os.path.exists(temp_out_path):
                        os.unlink(temp_out_path)
                except Exception as e:
                    logger.warning(f"Error cleaning up temp files: {e}")
                    
        except Exception as e:
            logger.error(f"Error normalizing audio content: {e}")
            return None

    def _get_audio_duration_wave(self, audio_content: bytes) -> float:
        """Get audio duration using wave module."""
        try:
            with io.BytesIO(audio_content) as buf:
                with wave.open(buf, 'rb') as wav:
                    frames = wav.getnframes()
                    rate = wav.getframerate()
                    channels = wav.getnchannels()
                    sampwidth = wav.getsampwidth()
                    
                    duration = frames / float(rate)
                    
                    logger.debug("Wave file details:")
                    logger.debug(f"- Frames: {frames:,}")
                    logger.debug(f"- Sample Rate: {rate:,} Hz")
                    logger.debug(f"- Channels: {channels}")
                    logger.debug(f"- Sample Width: {sampwidth * 8} bits")
                    logger.debug(f"- Duration: {duration:.3f}s")
                    
                    return duration
        except Exception as e:
            logger.warning(f"Wave duration detection failed: {str(e)}")
            return 0

    def get_audio_duration(self, audio_content: bytes) -> float:
        """Get duration of audio content in seconds."""
        if not audio_content:
            logger.error("No audio content provided")
            return 0
            
        # Inspect the audio content
        self._inspect_audio_content(audio_content)
        
        # Try to normalize the audio content if needed
        normalized_content = self._normalize_audio_content(audio_content)
        if normalized_content:
            audio_content = normalized_content
        
        # Get duration using wave
        duration = self._get_audio_duration_wave(audio_content)
        if duration > 0:
            return duration
            
        logger.error("Failed to detect audio duration")
        return 0
    
    def count_audio_content_tokens(self, audio_content: bytes, prompt_text: str = None) -> Dict[str, Any]:
        """Count tokens for audio content including prompt if provided."""
        if not audio_content:
            logger.error("No audio content provided")
            return {
                "audio_duration": 0,
                "audio_tokens": 0,
                "prompt_tokens": 0,
                "total_tokens": 0
            }
        
        logger.debug(f"Processing audio content of size: {len(audio_content):,} bytes")
        
        duration = self.get_audio_duration(audio_content)
        if duration == 0:
            logger.warning("Could not determine audio duration, using minimum token count")
            audio_tokens = self.AUDIO_TOKENS_PER_SECOND  # Minimum 1 second
        else:
            # Round up to nearest second to match Gemini's token counting behavior
            audio_tokens = int(self.AUDIO_TOKENS_PER_SECOND * max(1, round(duration)))
            
        prompt_tokens = self.count_text_tokens(prompt_text) if prompt_text else 0
        total_tokens = audio_tokens + prompt_tokens
        
        # Create compact token analysis
        token_data = {
            "Duration": f"{duration:.3f}s",
            "Audio Tokens": f"{audio_tokens:,} ({self.AUDIO_TOKENS_PER_SECOND}/s)",
            "Prompt Tokens": f"{prompt_tokens:,}",
            "Total Tokens": f"{total_tokens:,}"
        }
        
        # Create and display token table
        table = self._create_token_table("Audio Content Analysis", token_data)
        self.console.print(Panel(table, border_style="blue"))
        
        return {
            "audio_duration": duration,
            "audio_tokens": audio_tokens,
            "prompt_tokens": prompt_tokens,
            "total_tokens": total_tokens
        }

    def _create_token_table(self, title: str, data: Dict[str, Any]) -> Table:
        """Create a standardized token count table."""
        table = Table(title=title, box=None, show_header=True, padding=(0, 1))
        table.add_column("Component", style="cyan")
        table.add_column("Count", justify="right", style="green")
        for key, value in data.items():
            table.add_row(
                key.replace('_', ' ').title(),
                str(value)
            )
        return table
    
    def count_text_tokens(self, text: str) -> int:
        """Count tokens in text content."""
        if not text:
            return 0
        return self.model.count_tokens(text).total_tokens
    
    def count_chat_tokens(self, history: List[Dict[str, str]], next_message: str = None) -> int:
        """Count tokens in chat history and optionally include next message."""
        if next_message:
            total_tokens = self.model.count_tokens(history + [{"role": "user", "parts": next_message}]).total_tokens
            next_msg_tokens = self.model.count_tokens(next_message).total_tokens
            data = {
                "Chat History": total_tokens - next_msg_tokens,
                "Next Message": next_msg_tokens,
                "Total": total_tokens
            }
        else:
            total_tokens = self.model.count_tokens(history).total_tokens
            data = {"Chat History": total_tokens}
            
        table = self._create_token_table("Chat Token Analysis", data)
        self.console.print(Panel(table, border_style="blue"))
        return total_tokens
    
    def get_response_token_usage(self, response) -> Dict[str, int]:
        """Get token usage from a Gemini API response."""
        try:
            metadata = response.usage_metadata
            usage = {
                "Prompt Tokens": metadata.prompt_token_count,
                "Output Tokens": metadata.candidates_token_count,
                "Total Tokens": metadata.total_token_count
            }
            
            logger.info(f"Response Token Usage - Total: {usage['Total Tokens']}")
            
            table = self._create_token_table("Response Token Usage", usage)
            self.console.print(Panel(table, border_style="green"))
            
            return {
                "prompt_tokens": usage["Prompt Tokens"],
                "output_tokens": usage["Output Tokens"],
                "total_tokens": usage["Total Tokens"]
            }
        except Exception as e:
            logger.warning(f"Could not get token usage: {e}")
            return {"error": str(e)}

# Create a singleton instance
token_counter = TokenCounter()
