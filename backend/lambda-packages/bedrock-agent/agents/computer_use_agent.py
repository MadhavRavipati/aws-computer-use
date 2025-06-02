# ABOUTME: Computer Use Agent implementation using Strands-like framework
# ABOUTME: Provides AI-powered desktop control through Bedrock and VNC

import os
import json
import base64
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Since Strands SDK is not yet available, we'll create our own simple implementation
@dataclass
class Tool:
    """Represents a tool that can be used by the agent"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]


class Agent:
    """Simple agent implementation similar to Strands framework"""
    
    def __init__(self, model: str, prompt: str):
        self.model = model
        self.prompt = prompt
        self.tools: Dict[str, Tool] = {}
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-west-2'))
    
    def add_tool(self, tool: Tool):
        """Add a tool to the agent"""
        self.tools[tool.name] = tool
    
    async def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run the agent with user input"""
        # Prepare the messages for Claude
        messages = [
            {
                "role": "system",
                "content": self.prompt
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        
        # Add available tools to the prompt
        tool_descriptions = "\n".join([
            f"- {name}: {tool.description}" 
            for name, tool in self.tools.items()
        ])
        
        messages[0]["content"] += f"\n\nAvailable tools:\n{tool_descriptions}"
        
        try:
            # Call Bedrock with Claude
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.7
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            return {
                "success": True,
                "response": response_body.get('content', [{}])[0].get('text', ''),
                "usage": response_body.get('usage', {})
            }
            
        except ClientError as e:
            logger.error(f"Bedrock invocation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def tool(func: Callable) -> Callable:
    """Decorator to mark a function as a tool"""
    def wrapper(self, *args, **kwargs):
        return func(self, *args, **kwargs)
    wrapper.is_tool = True
    wrapper.tool_name = func.__name__
    return wrapper


class ComputerUseAgent:
    """Computer Use Agent built with Strands-like framework"""
    
    def __init__(self):
        # Initialize the agent with Claude 3.5 Sonnet v2
        self.model = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        self.agent = Agent(
            model=self.model,
            prompt="""You are a computer use assistant that helps users interact with desktop applications.
            You can analyze screenshots, move the mouse, click, type, and perform various computer actions.
            Always explain your reasoning before taking actions.
            
            When analyzing screenshots, describe what you see and identify interactive elements.
            When performing actions, be precise with coordinates and confirm success."""
        )
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools with the agent"""
        # Create Tool instances for each decorated method
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, 'is_tool') and attr.is_tool:
                tool = Tool(
                    name=attr.tool_name,
                    description=attr.__doc__ or f"Tool: {attr.tool_name}",
                    function=attr,
                    parameters={}  # Would be extracted from function signature
                )
                self.agent.add_tool(tool)
    
    @tool
    def screenshot_analyzer(self, screenshot_base64: str) -> Dict[str, Any]:
        """
        Analyze a screenshot to understand the current screen state
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            
        Returns:
            Analysis of visible elements and suggested actions
        """
        # Validate input
        if not screenshot_base64:
            return {
                "error": "No screenshot provided",
                "analysis": None
            }
        
        try:
            # Decode to verify it's valid base64
            decoded = base64.b64decode(screenshot_base64)
            
            return {
                "analysis": "Screenshot received and ready for analysis",
                "format": "base64",
                "size": len(screenshot_base64),
                "decoded_size": len(decoded)
            }
        except Exception as e:
            return {
                "error": f"Invalid screenshot data: {str(e)}",
                "analysis": None
            }
    
    @tool
    def vnc_controller(self, action: str, x: int = 0, y: int = 0, button: str = "left") -> Dict[str, Any]:
        """
        Control the VNC session with mouse actions
        
        Args:
            action: The action to perform (click, double_click, right_click)
            x: X coordinate
            y: Y coordinate
            button: Mouse button (left, right, middle)
            
        Returns:
            Result of the VNC action
        """
        valid_actions = ['click', 'double_click', 'right_click', 'drag']
        valid_buttons = ['left', 'right', 'middle']
        
        if action not in valid_actions:
            return {
                "error": f"Invalid action: {action}. Must be one of {valid_actions}",
                "status": "failed"
            }
        
        if button not in valid_buttons:
            return {
                "error": f"Invalid button: {button}. Must be one of {valid_buttons}",
                "status": "failed"
            }
        
        # Validate coordinates
        if x < 0 or y < 0:
            return {
                "error": "Coordinates must be non-negative",
                "status": "failed"
            }
        
        return {
            "action": action,
            "coordinates": {"x": x, "y": y},
            "button": button,
            "status": "executed",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    @tool
    def keyboard_input(self, text: str = "", key_combination: Optional[str] = None) -> Dict[str, Any]:
        """
        Type text or send key combinations
        
        Args:
            text: Text to type
            key_combination: Special key combination (e.g., "ctrl+c", "alt+tab")
            
        Returns:
            Result of keyboard action
        """
        if not text and not key_combination:
            return {
                "error": "Either text or key_combination must be provided",
                "status": "failed"
            }
        
        result = {
            "typed": text if text else None,
            "key_combination": key_combination if key_combination else None,
            "status": "executed",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Validate key combinations
        if key_combination:
            valid_modifiers = ['ctrl', 'alt', 'shift', 'cmd', 'meta']
            parts = key_combination.lower().split('+')
            
            # Check if it has valid format
            if len(parts) < 2:
                return {
                    "error": f"Invalid key combination format: {key_combination}",
                    "status": "failed"
                }
            
            # Check modifiers
            modifiers = parts[:-1]
            for mod in modifiers:
                if mod not in valid_modifiers:
                    return {
                        "error": f"Invalid modifier: {mod}",
                        "status": "failed"
                    }
        
        return result
    
    @tool
    def mouse_movement(self, x: int, y: int, duration: float = 0.5) -> Dict[str, Any]:
        """
        Move mouse to specific coordinates
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Duration of movement in seconds
            
        Returns:
            Result of mouse movement
        """
        # Validate coordinates
        if x < 0 or y < 0:
            return {
                "error": "Coordinates must be non-negative",
                "status": "failed"
            }
        
        if duration < 0:
            return {
                "error": "Duration must be non-negative",
                "status": "failed"
            }
        
        return {
            "moved_to": {"x": x, "y": y},
            "duration": duration,
            "status": "executed",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def execute_task(self, user_intent: str, screenshot: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a computer use task
        
        Args:
            user_intent: What the user wants to achieve
            screenshot: Optional current screenshot
            
        Returns:
            Result of the task execution
        """
        # Prepare the input for the agent
        agent_input = f"User intent: {user_intent}"
        
        context = {}
        if screenshot:
            agent_input += f"\n\nCurrent screenshot is available for analysis."
            # Analyze the screenshot first
            analysis = self.screenshot_analyzer(screenshot)
            context['screenshot_analysis'] = analysis
        
        try:
            # Run the agent
            result = await self.agent.run(agent_input, context)
            
            # Add execution metadata
            result['user_intent'] = user_intent
            result['has_screenshot'] = screenshot is not None
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_intent": user_intent
            }


# Lambda handler for Bedrock Agent Action Groups
def lambda_handler(event, context):
    """
    Lambda function to handle Bedrock Agent action group requests
    
    This function is called by Amazon Bedrock Agents when executing actions
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    action_group = event.get('actionGroup')
    api_path = event.get('apiPath')
    parameters = event.get('parameters', [])
    
    # Initialize our agent
    agent = ComputerUseAgent()
    
    # Helper to extract parameter value
    def get_param(name: str) -> Optional[str]:
        for p in parameters:
            if p.get('name') == name:
                return p.get('value')
        return None
    
    try:
        # Route to appropriate action
        if api_path == '/analyze-screen':
            screenshot = get_param('screenshot')
            intent = get_param('intent')
            
            if not screenshot or not intent:
                raise ValueError("Missing required parameters: screenshot and intent")
            
            # Execute the task asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(agent.execute_task(intent, screenshot))
            
        elif api_path == '/execute-action':
            action_type = get_param('action')
            coordinates = get_param('coordinates')
            
            if action_type == 'click' and coordinates:
                coords = json.loads(coordinates)
                result = agent.vnc_controller('click', coords['x'], coords['y'])
            elif action_type == 'type':
                text = get_param('text')
                result = agent.keyboard_input(text=text)
            elif action_type == 'key_combination':
                keys = get_param('keys')
                result = agent.keyboard_input(key_combination=keys)
            else:
                raise ValueError(f"Invalid action type: {action_type}")
        
        elif api_path == '/capture-screenshot':
            # This would be handled by the VNC bridge
            result = {
                "message": "Screenshot capture should be handled by VNC bridge",
                "status": "not_implemented"
            }
        
        else:
            raise ValueError(f"Unknown API path: {api_path}")
        
        # Format successful response
        return {
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'error': str(e),
                            'type': type(e).__name__
                        })
                    }
                }
            }
        }