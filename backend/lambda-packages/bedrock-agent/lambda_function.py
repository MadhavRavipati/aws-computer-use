#!/usr/bin/env python3
# ABOUTME: Lambda function entry point for Bedrock agent
# ABOUTME: Wraps the computer use agent for AWS Lambda

import sys
import os

# Add the parent directory to the path to import the agents module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.computer_use_agent import lambda_handler

# Re-export the lambda_handler
__all__ = ['lambda_handler']