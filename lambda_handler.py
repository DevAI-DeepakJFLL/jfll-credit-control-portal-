"""
AWS Lambda Entrypoint Handler for Jet Freight Logistics Credit Control CRM.
Compatible with AWS Lambda Function URLs and API Gateway HTTP API (Payload v2.0).
Routes incoming requests to the FastAPI application via Mangum and guarantees CORS.
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

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "86400",
}

def handler(event, context):
    if _wsgi_handler is None:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                **CORS_HEADERS
            },
            "body": json.dumps({"error": f"Handler initialization error: {_init_err}"})
        }
    
    # Fast-path for browser CORS preflight OPTIONS requests
    http_method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
    )
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

    response = _wsgi_handler(event, context)
    
    # Guarantee CORS headers on every response
    if isinstance(response, dict):
        if "headers" not in response or response["headers"] is None:
            response["headers"] = {}
        for k, v in CORS_HEADERS.items():
            if k not in response["headers"]:
                response["headers"][k] = v
                
    return response

lambda_handler = handler

__all__ = ["handler", "lambda_handler"]
