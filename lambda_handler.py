"""
AWS Lambda Entrypoint Handler for Jet Freight Logistics Credit Control CRM.
Compatible with AWS Lambda Function URLs and API Gateway HTTP API (Payload v2.0).
Routes incoming requests to the FastAPI application via Mangum.
"""
import os
import sys

# Ensure application source code is available in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app.main import app

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    lambda_handler = handler  # Alias for console compatibility
except ImportError:
    handler = None
    lambda_handler = None

__all__ = ["handler", "lambda_handler"]
