"""
AWS Lambda Entrypoint Handler for Jet Freight Logistics Credit Control CRM.
Compatible with AWS Lambda Function URLs and API Gateway HTTP API (Payload v2.0).
Routes incoming requests to the FastAPI application via Mangum.
CORS is handled directly by AWS Lambda Function URL gateway to prevent duplicate headers.
"""
import os
import sys
import json
import traceback

# Ensure application source code is available in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

_init_err = None
_wsgi_handler = None

try:
    from backend.app.main import app
    from mangum import Mangum
    _wsgi_handler = Mangum(app, lifespan="off")
except Exception as e:
    _init_err = f"{e}\n{traceback.format_exc()}"
    print(f"FATAL: Error initializing Lambda handler: {_init_err}")

def handler(event, context):
    if _wsgi_handler is None:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Handler initialization error: {_init_err}"})
        }
    return _wsgi_handler(event, context)

lambda_handler = handler

__all__ = ["handler", "lambda_handler"]
