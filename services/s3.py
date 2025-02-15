import os
from dotenv import load_dotenv
import boto3
import aiohttp
from datetime import datetime
from botocore.exceptions import ClientError
from typing import Tuple, Optional
import logging

# Load environment variables at module level
load_dotenv()

logger = logging.getLogger("s3_service")

class S3Service:
    def __init__(self):
        """Initialize S3 client with credentials from environment."""
        required_env_vars = {
            'AWS_ACCESS_KEY_ID': 'aws_access_key',
            'AWS_SECRET_ACCESS_KEY': 'aws_secret_key',
            'AWS_BUCKET_NAME': 'bucket_name',
            'AWS_REGION_NAME': 'aws_region_name'
        }
        
        # Set attributes and validate presence
        missing_vars = []
        for env_var, attr_name in required_env_vars.items():
            value = os.getenv(env_var)
            if env_var == 'AWS_REGION_NAME' and not value:
                value = 'us-east-2'  # Default region
            setattr(self, attr_name, value)
            if not value and env_var != 'AWS_REGION_NAME':
                missing_vars.append(env_var)
        
        if missing_vars:
            raise ValueError(f"Missing required AWS credentials: {', '.join(missing_vars)}")

    @property
    def s3_client(self):
        """Lazy initialization of S3 client."""
        if not hasattr(self, '_s3_client'):
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region_name
            )
            # Verify connection
            self._s3_client.head_bucket(Bucket=self.bucket_name)
        return self._s3_client

    async def download_file(self, file_key: str) -> bytes:
        """Download a file from S3 using a presigned URL."""
        url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': file_key},
            ExpiresIn=60
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download file: HTTP {response.status}")
                return await response.read()

    def get_file_content(self, file_key: str) -> bytes:
        """Get file content from S3 synchronously."""
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
        return response['Body'].read()

    def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for secure, time-limited access to an S3 object.
        
        Args:
            file_key: The key of the file in S3
            expires_in: Number of seconds until the URL expires (default: 1 hour)
            
        Returns:
            Presigned URL for the S3 object
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expires_in
            )
            logger.debug(f"Generated presigned URL for {file_key}, expires in {expires_in}s")
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise

    async def upload_file(
        self, 
        file_content: bytes, 
        filename: str,
        username: str = "anonymous",
        content_type: str = 'audio/wav',
        subfolder: str = 'uploads'
    ) -> Tuple[bool, str, Optional[str]]:
        """Upload a file to S3 and return success status, message, and file key."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_key = f"{subfolder}/{username}/{timestamp}_{filename.split('/')[-1]}"
            
            # Upload file with metadata
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'username': username,
                    'original_filename': filename,
                    'upload_timestamp': timestamp
                }
            )
            
            logger.info(f"Successfully uploaded {len(file_content)} bytes to S3: {file_key}")
            return True, "File uploaded successfully", file_key
            
        except ClientError as e:
            error_message = e.response['Error']['Message']
            logger.error(f"S3 upload failed: {error_message}")
            return False, f"S3 upload failed: {error_message}", None
            
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}")
            return False, f"Upload failed: {str(e)}", None

# Create singleton instance
s3_service = S3Service()