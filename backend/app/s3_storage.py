"""
AWS S3 Persistence Helper for Jet Freight Logistics Credit Control CRM.
Enables seamless synchronization of appraisals.db and generated CAM memos
when running in AWS Lambda, ECS, or EC2 with an S3 bucket configured.

Gracefully no-ops in local development or if AWS credentials/bucket are absent.
"""
import os
import json
import logging

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

def save_appraisal_record_to_s3(record: dict) -> bool:
    """Uploads individual appraisal record as JSON to S3 to guarantee multi-instance concurrency safety."""
    if not is_s3_enabled():
        return False
    
    s3 = get_s3_client()
    if not s3:
        return False

    record_key = record.get("docx_filename", "").replace(".docx", "").strip()
    if not record_key:
        return False

    s3_key = f"records/{record_key}.json"
    try:
        s3.put_object(
            Bucket=S3_DATA_BUCKET,
            Key=s3_key,
            Body=json.dumps(record, default=str).encode("utf-8"),
            ContentType="application/json"
        )
        logger.info(f"Saved atomic appraisal record to s3://{S3_DATA_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        logger.warning(f"Non-critical: Failed to save atomic appraisal record to S3: {e}")
        return False

def reconcile_records_from_s3(conn) -> int:
    """Reconciles individual records from S3 into local SQLite to prevent loss in multi-container setups."""
    if not is_s3_enabled():
        return 0
    
    s3 = get_s3_client()
    if not s3:
        return 0

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT docx_filename FROM appraisals")
        existing_filenames = {row[0] for row in cursor.fetchall()}

        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=S3_DATA_BUCKET, Prefix="records/")

        synced = 0
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj.get("Key", "")
                if not key.endswith(".json"):
                    continue
                expected_docx = os.path.basename(key).replace(".json", ".docx")
                if expected_docx not in existing_filenames:
                    try:
                        resp = s3.get_object(Bucket=S3_DATA_BUCKET, Key=key)
                        data = json.loads(resp["Body"].read().decode("utf-8"))
                        cursor.execute('''
                            INSERT OR IGNORE INTO appraisals (
                                customer_name, crif_credit_limit, credit_days, salesperson,
                                type_of_company, risk_grade, docx_filename, source_pdf, access_token, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            data.get("customer_name", "Unknown"),
                            data.get("crif_credit_limit", "₹ 0.00"),
                            data.get("credit_days", "30"),
                            data.get("salesperson", "Unassigned"),
                            data.get("type_of_company", "Proprietorship"),
                            data.get("risk_grade", "N/A"),
                            data.get("docx_filename", expected_docx),
                            data.get("source_pdf"),
                            data.get("access_token"),
                            data.get("created_at")
                        ))
                        existing_filenames.add(expected_docx)
                        synced += 1
                    except Exception as err:
                        logger.warning(f"Could not parse remote record {key}: {err}")
        if synced > 0:
            conn.commit()
            logger.info(f"Reconciled {synced} remote appraisal records from S3 into local database.")
        return synced
    except Exception as e:
        logger.warning(f"Notice: S3 record reconciliation skipped: {e}")
        return 0
