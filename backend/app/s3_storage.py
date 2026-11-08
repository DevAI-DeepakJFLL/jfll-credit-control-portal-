"""
AWS S3 Persistence Helper for Jet Freight Logistics Credit Control CRM.
Enables seamless synchronization of appraisals.db and generated CAM memos
when running in AWS Lambda, ECS, or EC2 with an S3 bucket configured.

Gracefully no-ops in local development or if AWS credentials/bucket are absent.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger("s3_storage")

S3_DATA_BUCKET = os.getenv("S3_DATA_BUCKET", "").strip()
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2").strip()

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception

_s3_client = None

def get_s3_client():
    global _s3_client
    if not BOTO3_AVAILABLE:
        return None
    if _s3_client is None:
        try:
            _s3_client = boto3.client("s3", region_name=AWS_REGION)
        except Exception as e:
            logger.warning(f"Could not initialize S3 client: {e}")
            _s3_client = None
    return _s3_client

def is_s3_enabled() -> bool:
    return bool(BOTO3_AVAILABLE and S3_DATA_BUCKET)

def sync_db_from_s3(local_db_path: str) -> bool:
    """Downloads appraisals.db from S3 if available and not present locally."""
    if not is_s3_enabled():
        return False
    
    s3 = get_s3_client()
    if not s3:
        return False

    s3_key = "database/appraisals.db"
    try:
        os.makedirs(os.path.dirname(local_db_path), exist_ok=True)
        # Check if remote DB exists
        s3.head_object(Bucket=S3_DATA_BUCKET, Key=s3_key)
        s3.download_file(S3_DATA_BUCKET, s3_key, local_db_path)
        logger.info(f"Successfully downloaded appraisals.db from s3://{S3_DATA_BUCKET}/{s3_key}")
        return True
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "404":
            logger.info("No remote appraisals.db found in S3. A fresh database will be initialized.")
        else:
            logger.warning(f"Notice: Failed to fetch DB from S3 ({e}). Using local store.")
        return False
    except Exception as e:
        logger.warning(f"Non-critical notice downloading DB from S3: {e}")
        return False

def sync_db_to_s3(local_db_path: str) -> bool:
    """Uploads local appraisals.db to S3 bucket for persistent durability."""
    if not is_s3_enabled():
        return False
    
    s3 = get_s3_client()
    if not s3 or not os.path.exists(local_db_path):
        return False

    s3_key = "database/appraisals.db"
    try:
        s3.upload_file(local_db_path, S3_DATA_BUCKET, s3_key)
        logger.info(f"Successfully synced appraisals.db to s3://{S3_DATA_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to backup appraisals.db to S3: {e}")
        return False

def upload_memo_to_s3(filename: str, local_path: str) -> bool:
    """Uploads generated DOCX memorandum to S3 for durability across ephemeral containers."""
    if not is_s3_enabled():
        return False
    
    s3 = get_s3_client()
    if not s3 or not os.path.exists(local_path):
        return False

    s3_key = f"memos/{filename}"
    try:
        s3.upload_file(
            local_path,
            S3_DATA_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        )
        logger.info(f"Uploaded DOCX memo to s3://{S3_DATA_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        logger.warning(f"Non-critical: Failed to upload memo to S3: {e}")
        return False

def download_memo_from_s3(filename: str, dest_path: str) -> bool:
    """Retrieves a DOCX memorandum from S3 if missing from local container disk."""
    if not is_s3_enabled():
        return False
    
    s3 = get_s3_client()
    if not s3:
        return False

    s3_key = f"memos/{filename}"
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        s3.download_file(S3_DATA_BUCKET, s3_key, dest_path)
        logger.info(f"Downloaded DOCX memo from s3://{S3_DATA_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        logger.info(f"Notice: Memo {s3_key} not retrieved from S3: {e}")
        return False
