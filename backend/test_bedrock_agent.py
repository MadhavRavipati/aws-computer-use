#!/usr/bin/env python3
# ABOUTME: Test script for Computer Use Agent with real Bedrock
# ABOUTME: Tests agent tools and Bedrock integration

import json
import os
import sys
import boto3
import base64
from io import BytesIO
from PIL import Image

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the agent
from agents.computer_use_agent import ComputerUseAgent

# Set AWS region
os.environ['AWS_REGION'] = 'us-west-2'

def create_test_screenshot():
    """Create a test screenshot"""
    # Create a simple test image
    img = Image.new('RGB', (1920, 1080), color='white')
    
    # Add some text (requires pillow with font support, so keeping it simple)
    # Just create a colored rectangle to simulate a window
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Draw a "browser window"
    draw.rectangle([100, 100, 1000, 700], fill='lightblue', outline='black')
    # Draw a "button"
    draw.rectangle([400, 400, 600, 450], fill='green', outline='black')
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

def test_bedrock_access():
    """Test direct Bedrock access"""
    print("\n=== Testing Bedrock access ===")
    
    bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
    
    try:
        # Test with a simple prompt
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": "Say 'Hello from Bedrock' and nothing else."
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        print(f"Bedrock response: {content}")
        return True
        
    except Exception as e:
        print(f"Error accessing Bedrock: {str(e)}")
        if "no identity-based policy allows" in str(e):
            print("Note: You may need to request access to Claude 3.5 Sonnet in Bedrock console")
        return False

def test_agent_tools():
    """Test agent tool functionality"""
    print("\n=== Testing Agent Tools ===")
    
    agent = ComputerUseAgent()
    
    # Test screenshot analyzer
    print("\n1. Testing screenshot analyzer tool:")
    screenshot = create_test_screenshot()
    result = agent.screenshot_analyzer(screenshot)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test VNC controller
    print("\n2. Testing VNC controller tool:")
    result = agent.vnc_controller('click', 500, 425)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test keyboard input
    print("\n3. Testing keyboard input tool:")
    result = agent.keyboard_input('Hello World')
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test mouse movement
    print("\n4. Testing mouse movement tool:")
    result = agent.mouse_movement(800, 600, 1.0)
    print(f"Result: {json.dumps(result, indent=2)}")

def test_agent_with_bedrock():
    """Test full agent with Bedrock integration"""
    print("\n=== Testing Agent with Bedrock ===")
    
    # First check if we have Bedrock access
    if not test_bedrock_access():
        print("Skipping agent test due to Bedrock access issues")
        return
    
    agent = ComputerUseAgent()
    screenshot = create_test_screenshot()
    
    try:
        # Create a simple task
        print("\nTesting agent task execution:")
        print("User intent: Click the green button")
        
        # Note: The actual agent execution would require the Strands SDK
        # For now, we'll test the individual components
        print("\nAgent components are ready. Full execution requires Strands SDK.")
        
    except Exception as e:
        print(f"Error in agent execution: {str(e)}")

def test_lambda_handler():
    """Test the Lambda handler function"""
    print("\n=== Testing Lambda Handler ===")
    
    from agents.computer_use_agent import lambda_handler
    
    # Test analyze-screen endpoint
    event = {
        'actionGroup': 'computer-control',
        'apiPath': '/analyze-screen',
        'parameters': [
            {'name': 'screenshot', 'value': create_test_screenshot()},
            {'name': 'intent', 'value': 'Find and click the submit button'}
        ]
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Lambda response: {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"Error in lambda handler: {str(e)}")

def main():
    """Run all tests"""
    print("Starting Computer Use Agent tests with real AWS services")
    print(f"Region: {os.environ.get('AWS_REGION')}")
    
    # Test Bedrock access
    test_bedrock_access()
    
    # Test agent tools
    test_agent_tools()
    
    # Test Lambda handler
    test_lambda_handler()
    
    # Test full agent (if Bedrock is available)
    # test_agent_with_bedrock()

if __name__ == '__main__':
    main()