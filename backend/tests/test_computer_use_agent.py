# ABOUTME: Test suite for Computer Use Agent with Strands framework
# ABOUTME: Tests agent initialization, tool registration, and action execution

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import base64
from typing import Dict, Any

from agents.computer_use_agent import ComputerUseAgent, Agent, Tool, tool, lambda_handler
from functions.session_manager import lambda_handler as session_lambda_handler


class TestComputerUseAgent:
    """Test suite for Computer Use Agent"""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock Bedrock client for testing"""
        client = Mock()
        client.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{'text': 'Test response'}]
            }).encode())
        }
        return client
    
    @pytest.fixture
    def sample_screenshot(self):
        """Sample base64 encoded screenshot for testing"""
        # Create a small test image
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def test_agent_initialization(self):
        """Test that agent initializes with correct configuration"""
        agent = ComputerUseAgent()
        
        assert agent.model == 'anthropic.claude-3-5-sonnet-20241022-v2:0'
        assert agent.agent is not None
        assert isinstance(agent.agent, Agent)
        assert len(agent.agent.tools) > 0
    
    def test_screenshot_analyzer_tool(self, sample_screenshot):
        """Test screenshot analyzer tool functionality"""
        agent = ComputerUseAgent()
        result = agent.screenshot_analyzer(sample_screenshot)
        
        assert result['analysis'] == "Screenshot received and ready for analysis"
        assert result['format'] == 'base64'
        assert result['size'] > 0
        assert 'decoded_size' in result
    
    def test_vnc_controller_click_action(self):
        """Test VNC controller click action"""
        agent = ComputerUseAgent()
        result = agent.vnc_controller('click', 100, 200, 'left')
        
        assert result['action'] == 'click'
        assert result['coordinates'] == {'x': 100, 'y': 200}
        assert result['button'] == 'left'
        assert result['status'] == 'executed'
    
    def test_keyboard_input_tool(self):
        """Test keyboard input tool"""
        agent = ComputerUseAgent()
        
        # Test typing text
        result = agent.keyboard_input(text="Hello World")
        assert result['typed'] == "Hello World"
        assert result['status'] == 'executed'
        
        # Test key combination
        result = agent.keyboard_input(key_combination="ctrl+c")
        assert result['key_combination'] == "ctrl+c"
        assert result['status'] == 'executed'
    
    def test_mouse_movement_tool(self):
        """Test mouse movement tool"""
        agent = ComputerUseAgent()
        result = agent.mouse_movement(500, 300, 1.0)
        
        assert result['moved_to'] == {'x': 500, 'y': 300}
        assert result['duration'] == 1.0
        assert result['status'] == 'executed'
    
    @pytest.mark.asyncio
    async def test_agent_execute_task(self, mock_bedrock_client, sample_screenshot):
        """Test agent task execution flow"""
        with patch('agents.computer_use_agent.boto3.client', return_value=mock_bedrock_client):
            agent = ComputerUseAgent()
            result = await agent.execute_task("Click the submit button", sample_screenshot)
            
            assert 'user_intent' in result
            assert result['user_intent'] == "Click the submit button"
            assert result['has_screenshot'] is True
    
    def test_agent_error_handling(self):
        """Test agent error handling and retries"""
        agent = ComputerUseAgent()
        
        # Test invalid action
        result = agent.vnc_controller('invalid_action', 0, 0)
        assert result['status'] == 'failed'
        assert 'error' in result
        
        # Test invalid coordinates
        result = agent.vnc_controller('click', -1, -1)
        assert result['status'] == 'failed'
        assert 'error' in result


class TestLambdaHandler:
    """Test suite for Lambda handler functions"""
    
    @pytest.fixture
    def lambda_context(self):
        """Mock Lambda context"""
        context = Mock()
        context.request_id = "test-request-id"
        context.function_name = "computer-use-agent-handler"
        context.memory_limit_in_mb = 1024
        context.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789012:function:test"
        return context
    
    @patch('agents.computer_use_agent.boto3.client')
    def test_bedrock_agent_action_group_handler(self, mock_boto_client, lambda_context):
        """Test Bedrock agent action group Lambda handler"""
        # Mock Bedrock response
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{'text': 'I will click the submit button'}]
            }).encode())
        }
        mock_boto_client.return_value = mock_bedrock
        
        event = {
            'actionGroup': 'computer-control',
            'apiPath': '/analyze-screen',
            'parameters': [
                {'name': 'screenshot', 'value': 'base64_image_data'},
                {'name': 'intent', 'value': 'Click submit button'}
            ]
        }
        
        result = lambda_handler(event, lambda_context)
        
        assert result['response']['httpStatusCode'] == 200
        assert result['response']['actionGroup'] == 'computer-control'
        assert result['response']['apiPath'] == '/analyze-screen'
    
    def test_session_manager_create_session(self, lambda_context):
        """Test session manager create session endpoint"""
        event = {
            'httpMethod': 'POST',
            'path': '/sessions',
            'body': json.dumps({
                'user_id': 'test-user-123'
            })
        }
        
        # Test will be implemented once we create the handler
        pass
    
    def test_session_manager_delete_session(self, lambda_context):
        """Test session manager delete session endpoint"""
        event = {
            'httpMethod': 'DELETE',
            'path': '/sessions/test-session-id'
        }
        
        # Test will be implemented once we create the handler
        pass


class TestVNCBridge:
    """Test suite for VNC Bridge service"""
    
    @pytest.fixture
    def vnc_client(self):
        """Mock VNC client"""
        return Mock()
    
    def test_vnc_bridge_connection(self, vnc_client):
        """Test VNC bridge connection initialization"""
        # Test will be implemented once we create the bridge
        pass
    
    def test_vnc_bridge_screenshot_capture(self, vnc_client):
        """Test VNC screenshot capture"""
        # Test will be implemented once we create the bridge
        pass
    
    def test_vnc_bridge_mouse_click(self, vnc_client):
        """Test VNC mouse click functionality"""
        # Test will be implemented once we create the bridge
        pass
    
    def test_vnc_bridge_keyboard_input(self, vnc_client):
        """Test VNC keyboard input"""
        # Test will be implemented once we create the bridge
        pass
    
    @pytest.mark.asyncio
    async def test_websocket_streaming(self):
        """Test WebSocket streaming functionality"""
        # Test will be implemented once we create the bridge
        pass


class TestIntegration:
    """Integration tests for the complete flow"""
    
    @pytest.mark.integration
    def test_end_to_end_click_action(self):
        """Test complete flow: intent -> agent -> VNC -> result"""
        # This will test the full integration once all components are ready
        pass
    
    @pytest.mark.integration
    def test_multi_step_workflow(self):
        """Test multi-step workflow execution"""
        # This will test complex workflows once all components are ready
        pass