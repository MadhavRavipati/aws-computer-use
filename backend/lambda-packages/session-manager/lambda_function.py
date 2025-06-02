#!/usr/bin/env python3
# ABOUTME: Lambda function entry point for session manager
# ABOUTME: Wraps the session manager module for AWS Lambda

import sys
import os

# Add the parent directory to the path to import the functions module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.session_manager import lambda_handler

# Re-export the lambda_handler
__all__ = ['lambda_handler']