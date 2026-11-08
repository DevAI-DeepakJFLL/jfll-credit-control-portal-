"""
AWS Lambda Entrypoint Bridge.
Ensures seamless compatibility when the AWS Console Handler is configured as:
- 'lambda_function.lambda_handler' OR
- 'lambda_function.handler'
"""
from lambda_handler import handler, lambda_handler

__all__ = ["handler", "lambda_handler"]
