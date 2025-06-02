# ABOUTME: WebSocket handler Lambda function for VNC streaming
# ABOUTME: Manages WebSocket connections and routes messages to ECS tasks

import json
import boto3
import os
import time
from typing import Dict, Any

# Initialize AWS clients
apigateway = boto3.client('apigatewaymanagementapi')
dynamodb = boto3.resource('dynamodb')
ecs = boto3.client('ecs')

# Environment variables
CONNECTIONS_TABLE = os.environ.get('CONNECTIONS_TABLE', 'computer-use-connections-dev')
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'computer-use-sessions-dev')
ECS_CLUSTER = os.environ.get('ECS_CLUSTER', 'computer-use-dev')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for WebSocket events
    """
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')
    
    if route_key == '$connect':
        return handle_connect(connection_id, event)
    elif route_key == '$disconnect':
        return handle_disconnect(connection_id)
    elif route_key == '$default':
        return handle_message(connection_id, event)
    else:
        return {'statusCode': 400, 'body': 'Invalid route'}

def handle_connect(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle new WebSocket connections
    """
    # Get session ID from query parameters
    query_params = event.get('queryStringParameters', {})
    session_id = query_params.get('sessionId')
    
    if not session_id:
        return {'statusCode': 400, 'body': 'Missing sessionId parameter'}
    
    # Verify session exists
    sessions_table = dynamodb.Table(SESSIONS_TABLE)
    try:
        response = sessions_table.get_item(Key={'session_id': session_id})
        if 'Item' not in response:
            return {'statusCode': 404, 'body': 'Session not found'}
    except Exception as e:
        print(f"Error verifying session: {e}")
        return {'statusCode': 500, 'body': 'Internal error'}
    
    # Store connection
    connections_table = dynamodb.Table(CONNECTIONS_TABLE)
    try:
        connections_table.put_item(
            Item={
                'connection_id': connection_id,
                'session_id': session_id,
                'connected_at': int(time.time())
            }
        )
    except Exception as e:
        print(f"Error storing connection: {e}")
        return {'statusCode': 500, 'body': 'Failed to store connection'}
    
    return {'statusCode': 200, 'body': 'Connected'}

def handle_disconnect(connection_id: str) -> Dict[str, Any]:
    """
    Handle WebSocket disconnections
    """
    connections_table = dynamodb.Table(CONNECTIONS_TABLE)
    try:
        connections_table.delete_item(Key={'connection_id': connection_id})
    except Exception as e:
        print(f"Error removing connection: {e}")
    
    return {'statusCode': 200, 'body': 'Disconnected'}

def handle_message(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle WebSocket messages
    """
    # Get connection info
    connections_table = dynamodb.Table(CONNECTIONS_TABLE)
    try:
        response = connections_table.get_item(Key={'connection_id': connection_id})
        if 'Item' not in response:
            return {'statusCode': 404, 'body': 'Connection not found'}
        
        session_id = response['Item']['session_id']
    except Exception as e:
        print(f"Error getting connection: {e}")
        return {'statusCode': 500, 'body': 'Internal error'}
    
    # Parse message body
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
    except json.JSONDecodeError:
        return {'statusCode': 400, 'body': 'Invalid JSON'}
    
    # Route based on action
    if action == 'vnc_command':
        return handle_vnc_command(connection_id, session_id, body)
    elif action == 'get_screenshot':
        return handle_get_screenshot(connection_id, session_id)
    else:
        return {'statusCode': 400, 'body': f'Unknown action: {action}'}

def handle_vnc_command(connection_id: str, session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Forward VNC commands to the appropriate ECS task
    """
    # Get task ARN for session
    sessions_table = dynamodb.Table(SESSIONS_TABLE)
    try:
        response = sessions_table.get_item(Key={'session_id': session_id})
        if 'Item' not in response:
            return {'statusCode': 404, 'body': 'Session not found'}
        
        task_arn = response['Item'].get('task_arn')
        if not task_arn:
            return {'statusCode': 404, 'body': 'No task associated with session'}
    except Exception as e:
        print(f"Error getting session: {e}")
        return {'statusCode': 500, 'body': 'Internal error'}
    
    # TODO: Forward command to ECS task via VNC bridge API
    # For now, just acknowledge
    send_to_connection(connection_id, {
        'type': 'vnc_response',
        'status': 'command_received',
        'command': body.get('command')
    })
    
    return {'statusCode': 200, 'body': 'Command forwarded'}

def handle_get_screenshot(connection_id: str, session_id: str) -> Dict[str, Any]:
    """
    Get current screenshot from VNC session
    """
    # TODO: Fetch screenshot from ECS task
    # For now, send placeholder response
    send_to_connection(connection_id, {
        'type': 'screenshot',
        'data': 'base64_encoded_image_data_placeholder',
        'timestamp': context.request_time_epoch
    })
    
    return {'statusCode': 200, 'body': 'Screenshot sent'}

def send_to_connection(connection_id: str, data: Dict[str, Any]) -> None:
    """
    Send data to a WebSocket connection
    """
    endpoint_url = f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
    
    api_client = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=endpoint_url
    )
    
    try:
        api_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data)
        )
    except api_client.exceptions.GoneException:
        # Connection no longer exists
        connections_table = dynamodb.Table(CONNECTIONS_TABLE)
        connections_table.delete_item(Key={'connection_id': connection_id})
    except Exception as e:
        print(f"Error sending to connection: {e}")

# Lambda context placeholder for development
class Context:
    request_time_epoch = 1234567890

context = Context()