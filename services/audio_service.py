"""
Core audio processing service that handles audio uploads and processing.
Provides a clean, reusable interface for audio operations.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union
from fastapi import UploadFile, HTTPException, status
import tempfile
import logging
from .s3 import s3_service
from .audio_validation import audio_validator

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(exist_ok=True)
        
    async def process_audio(
        self,
        audio: Optional[UploadFile] = None,
        existing_audio_url: Optional[str] = None,
        validation_required: bool = True
    ) -> Tuple[bytes, str, Dict[str, Any]]:
        """
        Process audio from either upload or existing URL.
        Returns: (audio_content, file_url, validation_details)
        """
        temp_file = None
        try:
            if audio:
                file_content, file_url, validation_details = await self._handle_new_upload(audio, validation_required)
            elif existing_audio_url:
                file_content, file_url, validation_details = await self._handle_existing_audio(existing_audio_url)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either audio file or audio_url must be provided"
                )
                
            return file_content, file_url, validation_details
            
        finally:
            if temp_file and hasattr(temp_file, 'name'):
                await self._cleanup_temp_file(temp_file)

    async def _handle_new_upload(
        self,
        audio: UploadFile,
        validation_required: bool
    ) -> Tuple[bytes, str, Dict[str, Any]]:
        """Handle new audio upload with optional validation."""
        try:
            file_content = await audio.read()
            
            if validation_required:
                validation_details = await self._validate_audio(
                    file_content,
                    audio.content_type
                )
            else:
                validation_details = {"passed": True, "reason": "Validation skipped"}

            file_url = await self._upload_to_storage(
                file_content,
                audio.filename,
                audio.content_type
            )
            
            return file_content, file_url, validation_details
            
        except Exception as e:
            logger.error(f"Error processing new audio upload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process audio upload: {str(e)}"
            )

    async def _handle_existing_audio(self, audio_url: str) -> Tuple[bytes, str, Dict[str, Any]]:
        """Handle existing audio from URL."""
        try:
            file_content = await s3_service.download_file(audio_url)
            return file_content, audio_url, {"passed": True, "reason": "Using existing audio"}
        except Exception as e:
            logger.error(f"Error retrieving existing audio: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve existing audio: {str(e)}"
            )

    async def _validate_audio(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """Validate audio content."""
        with tempfile.NamedTemporaryFile(suffix='.wav', dir=self.temp_dir, delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            return await audio_validator.validate_audio(Path(temp_file.name), content_type)

    async def _upload_to_storage(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Upload to storage and return URL."""
        success, message, file_key = await s3_service.upload_file(
            file_content=file_content,
            filename=filename,
            content_type=content_type
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to storage: {message}"
            )
            
        return s3_service.get_presigned_url(file_key, expires_in=3600)

    async def _cleanup_temp_file(self, temp_file: tempfile.NamedTemporaryFile) -> None:
        """Clean up temporary file."""
        try:
            temp_file_path = Path(temp_file.name)
            temp_file.close()
            if temp_file_path.exists():
                temp_file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to clean up temp file: {e}")
