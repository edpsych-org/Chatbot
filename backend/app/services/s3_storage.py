"""
AWS S3 storage service.

Replaces the earlier MinIO integration. One boto3 client, three buckets
(iq-tests / reports / temp) configurable via env, plus thin helpers for
upload / download / delete / presigned URL.

Reads config from app.core.config.settings:
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
    S3_BUCKET_IQ_TESTS, S3_BUCKET_REPORTS, S3_BUCKET_TEMP
    S3_ENDPOINT_URL  (optional; blank = default AWS)

If the access key is unset the service goes into "dev mode" and logs
what it would have done instead of raising, so local development
without AWS credentials still works.
"""

from __future__ import annotations

import logging
import uuid
from typing import BinaryIO, Optional

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Storage:
    """Wrapper around boto3 S3 client with the app's buckets baked in."""

    def __init__(self) -> None:
        self.region = settings.AWS_REGION or "eu-west-2"
        self.bucket_iq_tests = settings.S3_BUCKET_IQ_TESTS
        self.bucket_reports = settings.S3_BUCKET_REPORTS
        self.bucket_temp = settings.S3_BUCKET_TEMP

        self._enabled = bool(
            settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY
        )

        if self._enabled:
            client_kwargs: dict = {
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": self.region,
                "config": BotoConfig(signature_version="s3v4"),
            }
            if settings.S3_ENDPOINT_URL:
                client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

            self.client = boto3.client("s3", **client_kwargs)
            logger.info(
                "S3Storage initialised region=%s iq=%s reports=%s temp=%s",
                self.region,
                self.bucket_iq_tests or "<unset>",
                self.bucket_reports or "<unset>",
                self.bucket_temp or "<unset>",
            )
        else:
            self.client = None
            logger.warning(
                "S3Storage disabled — AWS_ACCESS_KEY_ID not set. Uploads will log only."
            )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    @property
    def enabled(self) -> bool:
        """True if credentials are configured and client is ready."""
        return self._enabled

    def check_health(self, bucket: Optional[str] = None) -> bool:
        """Verify the target bucket is reachable. Returns False on any error."""
        if not self._enabled:
            return False
        target = bucket or self.bucket_iq_tests
        if not target:
            return False
        try:
            self.client.head_bucket(Bucket=target)
            return True
        except ClientError as e:
            logger.warning("S3 head_bucket(%s) failed: %s", target, e)
            return False

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------
    @staticmethod
    def iq_test_key(student_id: str, extension: str) -> str:
        """Canonical key for IQ test uploads: iq-tests/<student>/<uuid>.<ext>"""
        ext = extension.lstrip(".") or "bin"
        return f"iq-tests/{student_id}/{uuid.uuid4()}.{ext}"

    @staticmethod
    def report_key(student_id: str, extension: str = "pdf") -> str:
        """Canonical key for generated reports."""
        ext = extension.lstrip(".") or "pdf"
        return f"reports/{student_id}/{uuid.uuid4()}.{ext}"

    # ------------------------------------------------------------------
    # Upload / download / delete
    # ------------------------------------------------------------------
    def upload_bytes(
        self,
        data: bytes,
        key: str,
        bucket: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[str]:
        """
        Upload a raw bytes payload. Returns the object key on success,
        None on failure or when disabled.
        """
        target = bucket or self.bucket_iq_tests
        if not self._enabled:
            logger.info(
                "[S3 DEV] would upload %d bytes to s3://%s/%s",
                len(data),
                target,
                key,
            )
            return key  # still return a key so callers can record it

        if not target:
            logger.error("upload_bytes: no bucket configured")
            return None

        extra: dict = {}
        if content_type:
            extra["ContentType"] = content_type

        try:
            self.client.put_object(Bucket=target, Key=key, Body=data, **extra)
            logger.info("S3 put_object OK s3://%s/%s (%d bytes)", target, key, len(data))
            return key
        except ClientError as e:
            logger.error("S3 put_object failed s3://%s/%s: %s", target, key, e)
            return None

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        bucket: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[str]:
        """Stream-upload a file-like object."""
        target = bucket or self.bucket_iq_tests
        if not self._enabled:
            logger.info("[S3 DEV] would stream-upload to s3://%s/%s", target, key)
            return key
        if not target:
            logger.error("upload_fileobj: no bucket configured")
            return None
        extra_args: dict = {}
        if content_type:
            extra_args["ContentType"] = content_type
        try:
            self.client.upload_fileobj(
                Fileobj=fileobj, Bucket=target, Key=key, ExtraArgs=extra_args
            )
            logger.info("S3 upload_fileobj OK s3://%s/%s", target, key)
            return key
        except ClientError as e:
            logger.error("S3 upload_fileobj failed s3://%s/%s: %s", target, key, e)
            return None

    def download_bytes(
        self, key: str, bucket: Optional[str] = None
    ) -> Optional[bytes]:
        """Download an object as bytes. Returns None on failure or disabled."""
        target = bucket or self.bucket_iq_tests
        if not self._enabled:
            logger.info("[S3 DEV] would download s3://%s/%s", target, key)
            return None
        try:
            resp = self.client.get_object(Bucket=target, Key=key)
            return resp["Body"].read()
        except ClientError as e:
            logger.error("S3 get_object failed s3://%s/%s: %s", target, key, e)
            return None

    def delete(self, key: str, bucket: Optional[str] = None) -> bool:
        """Delete a single object. Returns True on success."""
        target = bucket or self.bucket_iq_tests
        if not self._enabled:
            logger.info("[S3 DEV] would delete s3://%s/%s", target, key)
            return True
        try:
            self.client.delete_object(Bucket=target, Key=key)
            logger.info("S3 delete OK s3://%s/%s", target, key)
            return True
        except ClientError as e:
            logger.error("S3 delete failed s3://%s/%s: %s", target, key, e)
            return False

    def presigned_url(
        self,
        key: str,
        bucket: Optional[str] = None,
        expires_in: int = 300,
    ) -> Optional[str]:
        """
        Generate a short-lived HTTPS URL the browser can fetch directly.
        Used by the reports-workspace UI to link to stored PDFs.
        """
        target = bucket or self.bucket_iq_tests
        if not self._enabled:
            logger.info("[S3 DEV] would presign s3://%s/%s", target, key)
            return None
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": target, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error("S3 presign failed s3://%s/%s: %s", target, key, e)
            return None


# Module-level singleton — import this rather than constructing a new client.
s3_storage = S3Storage()
