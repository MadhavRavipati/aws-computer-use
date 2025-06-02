# ABOUTME: CORS handler Lambda function for API Gateway OPTIONS requests
# ABOUTME: Returns proper CORS headers for browser compatibility

import json

def lambda_handler(event, context):
    """Handle CORS preflight requests"""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
            'Access-Control-Max-Age': '86400'
        },
        'body': json.dumps({'message': 'CORS preflight successful'})
    }