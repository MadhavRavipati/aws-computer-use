# ABOUTME: Lambda authorizer for API Gateway authentication
# ABOUTME: Validates API keys and returns IAM policy

import json
import os
import boto3
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB table for API keys
dynamodb = boto3.resource('dynamodb')
api_keys_table = dynamodb.Table(os.environ.get('API_KEYS_TABLE', 'computer-use-api-keys-dev'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API Gateway Lambda Authorizer
    
    Validates API keys from Authorization header
    Returns IAM policy to allow/deny API access
    """
    logger.info(f"Authorization event: {json.dumps(event)}")
    
    # Extract token from event
    token = event.get('authorizationToken', '')
    method_arn = event.get('methodArn', '')
    
    # Validate token format (Bearer <api-key>)
    if not token.startswith('Bearer '):
        logger.warning("Invalid token format")
        raise Exception('Unauthorized')
    
    api_key = token.replace('Bearer ', '').strip()
    
    if not api_key:
        logger.warning("Empty API key")
        raise Exception('Unauthorized')
    
    # Validate API key
    principal_id, policy = validate_api_key(api_key, method_arn)
    
    if not principal_id:
        logger.warning(f"Invalid API key: {api_key[:8]}...")
        raise Exception('Unauthorized')
    
    return policy

def validate_api_key(api_key: str, method_arn: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate API key against DynamoDB
    
    Returns:
        Tuple of (principal_id, policy)
    """
    try:
        # Look up API key in DynamoDB
        response = api_keys_table.get_item(
            Key={'api_key': api_key}
        )
        
        key_data = response.get('Item')
        if not key_data:
            return None, None
        
        # Check if key is active
        if not key_data.get('active', False):
            logger.warning(f"Inactive API key: {api_key[:8]}...")
            return None, None
        
        # Check rate limits
        current_usage = key_data.get('usage_count', 0)
        rate_limit = key_data.get('rate_limit', 1000)
        
        if current_usage >= rate_limit:
            logger.warning(f"Rate limit exceeded for key: {api_key[:8]}...")
            return None, None
        
        # Update usage count
        api_keys_table.update_item(
            Key={'api_key': api_key},
            UpdateExpression='SET usage_count = usage_count + :inc, last_used = :now',
            ExpressionAttributeValues={
                ':inc': 1,
                ':now': int(context.aws_request_id)
            }
        )
        
        # Extract principal ID
        principal_id = key_data.get('user_id', 'user')
        
        # Build policy
        policy = generate_policy(
            principal_id,
            'Allow',
            method_arn,
            context={
                'user_id': principal_id,
                'api_key_id': key_data.get('key_id', ''),
                'tier': key_data.get('tier', 'basic')
            }
        )
        
        return principal_id, policy
        
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return None, None

def generate_policy(principal_id: str, effect: str, resource: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate IAM policy for API Gateway
    """
    auth_response = {
        'principalId': principal_id
    }
    
    if effect and resource:
        policy_document = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource.replace('/GET/', '/*/')  # Allow all methods
                }
            ]
        }
        auth_response['policyDocument'] = policy_document
    
    # Add context to pass additional info to Lambda functions
    if context:
        auth_response['context'] = context
    
    return auth_response

def create_api_key_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to create new API keys
    Should be called by admin users only
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id', 'anonymous')
        tier = body.get('tier', 'basic')
        
        # Generate new API key
        import uuid
        import hashlib
        
        # Generate a secure API key
        raw_key = f"{user_id}:{uuid.uuid4()}:{context.aws_request_id}"
        api_key = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Set rate limits based on tier
        rate_limits = {
            'basic': 1000,      # 1000 requests per day
            'standard': 10000,  # 10k requests per day
            'premium': 100000   # 100k requests per day
        }
        
        # Store in DynamoDB
        api_keys_table.put_item(
            Item={
                'api_key': api_key,
                'key_id': str(uuid.uuid4()),
                'user_id': user_id,
                'tier': tier,
                'rate_limit': rate_limits.get(tier, 1000),
                'usage_count': 0,
                'active': True,
                'created_at': int(context.aws_request_id),
                'expires_at': int(context.aws_request_id) + 365 * 24 * 60 * 60  # 1 year
            }
        )
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'api_key': api_key,
                'user_id': user_id,
                'tier': tier,
                'rate_limit': rate_limits.get(tier, 1000),
                'message': 'API key created successfully. Store this key securely as it cannot be retrieved again.'
            })
        }
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }