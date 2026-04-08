"""
Test package initialization.

Sets up environment variables before any test modules are imported.
This file is loaded by pytest before conftest.py.
"""

import os

# Set test environment variables BEFORE any application code is imported
os.environ.setdefault("POSTGRESQL_PWD", "test_password")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-openai-key-12345")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing-only")

# Prevent accidental AWS usage
os.environ.pop("AWS_EXECUTION_ENV", None)
os.environ.pop("AWS_SAM_LOCAL", None)
