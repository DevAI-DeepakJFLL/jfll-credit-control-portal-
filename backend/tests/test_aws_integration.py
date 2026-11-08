import unittest
import os
from fastapi.testclient import TestClient
from backend.app.main import app
import lambda_handler
from backend.app import s3_storage

class TestAWSIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_metadata(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("runtime", data)
        self.assertIn("s3_persistence", data)

    def test_lambda_handler_exists(self):
        self.assertIsNotNone(lambda_handler.handler)
        self.assertTrue(callable(lambda_handler.handler))

    def test_s3_storage_graceful_fallback(self):
        # When S3_DATA_BUCKET is not set or boto3 has no creds
        self.assertFalse(s3_storage.sync_db_from_s3("/tmp/non_existent.db"))
        self.assertFalse(s3_storage.sync_db_to_s3("/tmp/non_existent.db"))
        self.assertFalse(s3_storage.upload_memo_to_s3("memo.docx", "/tmp/non_existent.docx"))
        self.assertFalse(s3_storage.download_memo_from_s3("memo.docx", "/tmp/non_existent.docx"))

if __name__ == "__main__":
    unittest.main()
