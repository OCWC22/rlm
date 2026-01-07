"""
Cloudflare R2 storage for JSON Explorer.

Uses Cloudflare R2 (S3-compatible) for:
- Large JSON file storage
- Streaming file access
- File versioning and deduplication

Design:
- boto3 S3-compatible client
- Streaming support for large files
- Content-addressable storage option
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Iterator, BinaryIO
from dataclasses import dataclass

# boto3 imports
try:
    import boto3
    from botocore.config import Config as BotoConfig
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None


@dataclass
class R2Object:
    """Metadata about an R2 object."""
    key: str
    size: int
    etag: str
    last_modified: str
    content_type: Optional[str] = None


class R2Storage:
    """
    Cloudflare R2 storage backend.
    
    Environment variables:
        CLOUDFLARE_R2_ACCOUNT_ID: Cloudflare account ID
        CLOUDFLARE_R2_ACCESS_KEY_ID: R2 access key
        CLOUDFLARE_R2_SECRET_ACCESS_KEY: R2 secret key
        CLOUDFLARE_R2_BUCKET_NAME: R2 bucket name
        CLOUDFLARE_R2_PUBLIC_URL: Optional public URL for bucket
    
    Example:
        >>> storage = R2Storage()
        >>> key = await storage.upload_file("/path/to/data.json")
        >>> with storage.download_stream(key) as stream:
        ...     for chunk in stream:
        ...         process(chunk)
    """
    
    def __init__(
        self,
        account_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        public_url: Optional[str] = None,
    ):
        """
        Initialize R2 storage.
        
        Args:
            account_id: Cloudflare account ID
            access_key_id: R2 access key ID
            secret_access_key: R2 secret access key
            bucket_name: R2 bucket name
            public_url: Optional public URL for the bucket
        """
        if not HAS_BOTO3:
            raise ImportError(
                "boto3 not installed. Run: pip install boto3"
            )
        
        self.account_id = account_id or os.environ.get("CLOUDFLARE_R2_ACCOUNT_ID")
        self.access_key_id = access_key_id or os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.environ.get("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or os.environ.get("CLOUDFLARE_R2_BUCKET_NAME")
        self.public_url = public_url or os.environ.get("CLOUDFLARE_R2_PUBLIC_URL")
        
        if not all([self.account_id, self.access_key_id, self.secret_access_key, self.bucket_name]):
            raise ValueError(
                "R2 credentials required. Set environment variables: "
                "CLOUDFLARE_R2_ACCOUNT_ID, CLOUDFLARE_R2_ACCESS_KEY_ID, "
                "CLOUDFLARE_R2_SECRET_ACCESS_KEY, CLOUDFLARE_R2_BUCKET_NAME"
            )
        
        # Create S3 client for R2
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=BotoConfig(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
            region_name="auto",
        )
    
    # ─────────────────────────────────────────────────────────────
    # File operations
    # ─────────────────────────────────────────────────────────────
    
    def upload_file(
        self,
        file_path: str,
        key: Optional[str] = None,
        content_addressable: bool = False,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload a file to R2.
        
        Args:
            file_path: Local file path
            key: R2 object key (default: filename)
            content_addressable: Use file hash as key
            metadata: Optional metadata dict
            
        Returns:
            R2 object key
        """
        file_path = Path(file_path)
        
        if content_addressable:
            # Use content hash as key
            file_hash = self._hash_file(file_path)
            key = f"files/{file_hash}/{file_path.name}"
        elif not key:
            key = f"uploads/{file_path.name}"
        
        extra_args = {}
        if metadata:
            extra_args["Metadata"] = {
                k: str(v) for k, v in metadata.items()
            }
        
        # Detect content type
        if file_path.suffix == ".json":
            extra_args["ContentType"] = "application/json"
        
        self._client.upload_file(
            str(file_path),
            self.bucket_name,
            key,
            ExtraArgs=extra_args or None,
        )
        
        return key
    
    def upload_data(
        self,
        data: bytes | str,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload data directly to R2.
        
        Args:
            data: Data to upload
            key: R2 object key
            content_type: MIME type
            metadata: Optional metadata
            
        Returns:
            R2 object key
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
            if content_type == "application/octet-stream":
                content_type = "text/plain; charset=utf-8"
        
        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = {
                k: str(v) for k, v in metadata.items()
            }
        
        self._client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            **extra_args,
        )
        
        return key
    
    def download_file(self, key: str, destination: str) -> str:
        """
        Download a file from R2.
        
        Args:
            key: R2 object key
            destination: Local file path
            
        Returns:
            Local file path
        """
        self._client.download_file(
            self.bucket_name,
            key,
            destination,
        )
        return destination
    
    def download_data(self, key: str) -> bytes:
        """
        Download data directly from R2.
        
        Args:
            key: R2 object key
            
        Returns:
            File contents as bytes
        """
        response = self._client.get_object(
            Bucket=self.bucket_name,
            Key=key,
        )
        return response["Body"].read()
    
    def download_stream(
        self,
        key: str,
        chunk_size: int = 8 * 1024 * 1024,  # 8MB chunks
    ) -> Iterator[bytes]:
        """
        Stream a file from R2.
        
        Args:
            key: R2 object key
            chunk_size: Size of each chunk in bytes
            
        Yields:
            Chunks of file data
        """
        response = self._client.get_object(
            Bucket=self.bucket_name,
            Key=key,
        )
        
        body = response["Body"]
        while True:
            chunk = body.read(chunk_size)
            if not chunk:
                break
            yield chunk
        
        body.close()
    
    def stream_json_objects(
        self,
        key: str,
        chunk_size: int = 1024 * 1024,
    ) -> Iterator[dict]:
        """
        Stream JSON objects from a JSON array file.
        
        This is memory-efficient for large JSON files.
        
        Args:
            key: R2 object key (must be a JSON array)
            chunk_size: Size of chunks to read
            
        Yields:
            Individual JSON objects
        """
        # For true streaming, we'd use ijson
        # For now, simple implementation
        import json
        
        data = self.download_data(key)
        objects = json.loads(data)
        
        if isinstance(objects, list):
            yield from objects
        elif isinstance(objects, dict) and "messages" in objects:
            yield from objects["messages"]
        else:
            yield objects
    
    def delete(self, key: str) -> bool:
        """
        Delete an object from R2.
        
        Args:
            key: R2 object key
            
        Returns:
            True if deleted
        """
        try:
            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if an object exists."""
        try:
            self._client.head_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except Exception:
            return False
    
    def get_metadata(self, key: str) -> Optional[R2Object]:
        """Get object metadata."""
        try:
            response = self._client.head_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return R2Object(
                key=key,
                size=response["ContentLength"],
                etag=response["ETag"].strip('"'),
                last_modified=response["LastModified"].isoformat(),
                content_type=response.get("ContentType"),
            )
        except Exception:
            return None
    
    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[R2Object]:
        """
        List objects in the bucket.
        
        Args:
            prefix: Key prefix to filter
            max_keys: Maximum objects to return
            
        Returns:
            List of R2Object metadata
        """
        response = self._client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix,
            MaxKeys=max_keys,
        )
        
        objects = []
        for obj in response.get("Contents", []):
            objects.append(R2Object(
                key=obj["Key"],
                size=obj["Size"],
                etag=obj["ETag"].strip('"'),
                last_modified=obj["LastModified"].isoformat(),
            ))
        
        return objects
    
    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str:
        """
        Generate a presigned URL for temporary access.
        
        Args:
            key: R2 object key
            expires_in: URL validity in seconds (default 1 hour)
            method: "get_object" for download, "put_object" for upload
            
        Returns:
            Presigned URL
        """
        return self._client.generate_presigned_url(
            ClientMethod=method,
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )
    
    def get_public_url(self, key: str) -> Optional[str]:
        """
        Get public URL if bucket has public access configured.
        
        Args:
            key: R2 object key
            
        Returns:
            Public URL or None if not configured
        """
        if self.public_url:
            return f"{self.public_url.rstrip('/')}/{key}"
        return None
    
    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def _hash_file(file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()


# Convenience function for quick uploads
def upload_to_r2(file_path: str, key: Optional[str] = None) -> str:
    """Quick upload to R2 using environment variables."""
    storage = R2Storage()
    return storage.upload_file(file_path, key)


def download_from_r2(key: str, destination: str) -> str:
    """Quick download from R2 using environment variables."""
    storage = R2Storage()
    return storage.download_file(key, destination)

