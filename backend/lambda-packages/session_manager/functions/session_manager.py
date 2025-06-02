# ABOUTME: Session manager Lambda function for ECS task lifecycle
# ABOUTME: Handles creation, deletion, and status of desktop sessions

import os
import json
import uuid
import time
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types from DynamoDB"""
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0:
                return int(o)
            else:
                return float(o)
        return super(DecimalEncoder, self).default(o)

# Initialize AWS clients
ecs = boto3.client('ecs')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
TASK_DEFINITION = os.environ.get('TASK_DEFINITION')
SUBNETS = os.environ.get('SUBNETS', '').split(',')
SECURITY_GROUP = os.environ.get('SECURITY_GROUP')
SESSION_TABLE = os.environ.get('SESSION_TABLE')
TARGET_GROUP_ARN = os.environ.get('TARGET_GROUP_ARN')

# DynamoDB table
sessions_table = dynamodb.Table(SESSION_TABLE) if SESSION_TABLE else None


def lambda_handler(event, context):
    """
    Main Lambda handler for session management
    
    Handles:
    - POST /sessions - Create new session
    - GET /sessions/{id} - Get session status
    - DELETE /sessions/{id} - Terminate session
    - GET /sessions - List user sessions
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method'))
        path = event.get('path', event.get('rawPath', ''))
        
        if http_method == 'POST' and path == '/sessions':
            return create_session(event)
        elif http_method == 'GET' and '/sessions/' in path:
            session_id = path.split('/')[-1]
            return get_session_status(session_id)
        elif http_method == 'DELETE' and '/sessions/' in path:
            session_id = path.split('/')[-1]
            return terminate_session(session_id)
        elif http_method == 'GET' and path == '/sessions':
            return list_sessions(event)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
                },
                'body': json.dumps({'error': 'Not found'})
            }
    
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }


def create_session(event):
    """Create a new desktop session"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id', 'anonymous')
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create ECS task
        task_response = ecs.run_task(
            cluster=ECS_CLUSTER,
            taskDefinition=TASK_DEFINITION,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': SUBNETS,
                    'securityGroups': [SECURITY_GROUP],
                    'assignPublicIp': 'DISABLED'
                }
            },
            overrides={
                'containerOverrides': [
                    {
                        'name': 'desktop',
                        'environment': [
                            {
                                'name': 'SESSION_ID',
                                'value': session_id
                            },
                            {
                                'name': 'USER_ID',
                                'value': user_id
                            }
                        ]
                    }
                ]
            },
            tags=[
                {
                    'key': 'SessionId',
                    'value': session_id
                },
                {
                    'key': 'UserId',
                    'value': user_id
                }
            ]
        )
        
        # Extract task ARN
        if not task_response.get('tasks'):
            raise Exception("Failed to start ECS task")
        
        task_arn = task_response['tasks'][0]['taskArn']
        task_id = task_arn.split('/')[-1]
        
        # Store session in DynamoDB
        session_item = {
            'session_id': session_id,
            'user_id': user_id,
            'task_arn': task_arn,
            'task_id': task_id,
            'status': 'starting',
            'created_at': int(time.time()),
            'ttl': int(time.time()) + 3600,  # 1 hour TTL
            'cluster': ECS_CLUSTER
        }
        
        if sessions_table:
            sessions_table.put_item(Item=session_item)
        
        # Send metric
        cloudwatch.put_metric_data(
            Namespace='ComputerUse',
            MetricData=[
                {
                    'MetricName': 'SessionsCreated',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
        
        # Return session details
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'X-Session-Id': session_id,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'session_id': session_id,
                'status': 'starting',
                'task_id': task_id,
                'websocket_url': f"wss://uaakatj7z0.execute-api.us-west-2.amazonaws.com/dev?session_id={session_id}",
                'vnc_url': f"http://computer-use-dev-797992487.us-west-2.elb.amazonaws.com/vnc/{session_id}"
            })
        }
    
    except ClientError as e:
        logger.error(f"AWS error creating session: {e}")
        return {
            'statusCode': 503,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Service temporarily unavailable',
                'details': str(e)
            })
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }


def get_session_status(session_id):
    """Get status of a session"""
    try:
        # Get session from DynamoDB
        if sessions_table:
            response = sessions_table.get_item(Key={'session_id': session_id})
            session = response.get('Item')
            
            if not session:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Session not found'})
                }
            
            # Get current task status from ECS
            task_arn = session.get('task_arn')
            if task_arn:
                tasks = ecs.describe_tasks(
                    cluster=ECS_CLUSTER,
                    tasks=[task_arn]
                )
                
                if tasks.get('tasks'):
                    task = tasks['tasks'][0]
                    task_status = task.get('lastStatus', 'UNKNOWN')
                    
                    # Update session status
                    session['status'] = task_status.lower()
                    
                    # Get container details
                    containers = task.get('containers', [])
                    session['containers'] = [
                        {
                            'name': c.get('name'),
                            'status': c.get('lastStatus'),
                            'health': c.get('healthStatus')
                        }
                        for c in containers
                    ]
                    
                    # Get network details if running
                    if task_status == 'RUNNING':
                        attachments = task.get('attachments', [])
                        for attachment in attachments:
                            if attachment.get('type') == 'ElasticNetworkInterface':
                                details = attachment.get('details', [])
                                for detail in details:
                                    if detail.get('name') == 'privateIPv4Address':
                                        session['private_ip'] = detail.get('value')
                                        break
            
            return {
                'statusCode': 200,
                'body': json.dumps(session, cls=DecimalEncoder)
            }
        else:
            return {
                'statusCode': 503,
                'body': json.dumps({'error': 'Session storage not available'})
            }
    
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }


def terminate_session(session_id):
    """Terminate a session"""
    try:
        # Get session from DynamoDB
        if sessions_table:
            response = sessions_table.get_item(Key={'session_id': session_id})
            session = response.get('Item')
            
            if not session:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Session not found'})
                }
            
            # Stop ECS task
            task_arn = session.get('task_arn')
            if task_arn:
                ecs.stop_task(
                    cluster=ECS_CLUSTER,
                    task=task_arn,
                    reason=f'Session {session_id} terminated by user'
                )
            
            # Update session status
            sessions_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET #status = :status, terminated_at = :time',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'terminated',
                    ':time': int(time.time())
                }
            )
            
            # Send metric
            cloudwatch.put_metric_data(
                Namespace='ComputerUse',
                MetricData=[
                    {
                        'MetricName': 'SessionsTerminated',
                        'Value': 1,
                        'Unit': 'Count'
                    }
                ]
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Session {session_id} terminated successfully'
                })
            }
        else:
            return {
                'statusCode': 503,
                'body': json.dumps({'error': 'Session storage not available'})
            }
    
    except Exception as e:
        logger.error(f"Error terminating session: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }


def list_sessions(event):
    """List sessions for a user"""
    try:
        # Get user_id from query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        user_id = query_params.get('user_id', 'anonymous')
        
        if sessions_table:
            # Query sessions by user
            response = sessions_table.query(
                IndexName='user-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={
                    ':user_id': user_id
                },
                ScanIndexForward=False,  # Most recent first
                Limit=20
            )
            
            sessions = response.get('Items', [])
            
            # Filter out expired sessions
            current_time = int(time.time())
            active_sessions = [
                s for s in sessions 
                if s.get('ttl', 0) > current_time or s.get('status') == 'running'
            ]
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'sessions': active_sessions,
                    'count': len(active_sessions)
                }, cls=DecimalEncoder)
            }
        else:
            return {
                'statusCode': 503,
                'body': json.dumps({'error': 'Session storage not available'})
            }
    
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }