#!/usr/bin/env python3
# ABOUTME: Test script for session manager Lambda function
# ABOUTME: Tests with real AWS services instead of mocks

import json
import os
import sys
import boto3
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the lambda handler
from functions.session_manager import lambda_handler

# Set environment variables
os.environ['ECS_CLUSTER'] = 'computer-use-dev'
os.environ['ECS_SERVICE'] = 'desktop-service'
os.environ['TASK_DEFINITION'] = 'computer-use-desktop'
os.environ['SUBNETS'] = 'subnet-0c232ef0f6d6be46c,subnet-03ab5f77f4b51cc00'  # Use actual subnet IDs
os.environ['SECURITY_GROUP'] = 'sg-09b3f4c94bdd4f076'  # Will need to get actual SG
os.environ['SESSION_TABLE'] = 'computer-use-sessions-dev'
os.environ['AWS_REGION'] = 'us-west-2'

def test_list_sessions():
    """Test listing sessions"""
    print("\n=== Testing LIST sessions ===")
    
    event = {
        'httpMethod': 'GET',
        'path': '/sessions',
        'headers': {
            'x-user-id': 'test-user-001'
        }
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Status: {response['statusCode']}")
        print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_create_session():
    """Test creating a new session"""
    print("\n=== Testing CREATE session ===")
    
    event = {
        'httpMethod': 'POST',
        'path': '/sessions',
        'headers': {
            'x-user-id': 'test-user-001'
        },
        'body': json.dumps({
            'session_name': 'Test Session',
            'resolution': '1920x1080'
        })
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Status: {response['statusCode']}")
        body = json.loads(response['body'])
        print(f"Response: {json.dumps(body, indent=2)}")
        
        if response['statusCode'] == 200:
            return body.get('session_id')
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_get_session(session_id):
    """Test getting session status"""
    print(f"\n=== Testing GET session {session_id} ===")
    
    event = {
        'httpMethod': 'GET',
        'path': f'/sessions/{session_id}',
        'pathParameters': {
            'id': session_id
        },
        'headers': {
            'x-user-id': 'test-user-001'
        }
    }
    
    try:
        response = lambda_handler(event, {})
        print(f"Status: {response['statusCode']}")
        print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_direct_dynamodb():
    """Test direct DynamoDB access"""
    print("\n=== Testing direct DynamoDB access ===")
    
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('computer-use-sessions-dev')
    
    try:
        # List all items
        response = table.scan()
        print(f"Total items in table: {response['Count']}")
        
        for item in response['Items']:
            print(f"Session: {item.get('session_id')} - Status: {item.get('status')}")
            
    except Exception as e:
        print(f"Error accessing DynamoDB: {str(e)}")

def test_ecs_access():
    """Test ECS cluster access"""
    print("\n=== Testing ECS access ===")
    
    ecs = boto3.client('ecs', region_name='us-west-2')
    
    try:
        # Describe cluster
        response = ecs.describe_clusters(clusters=['computer-use-dev'])
        clusters = response.get('clusters', [])
        
        if clusters:
            cluster = clusters[0]
            print(f"Cluster: {cluster['clusterName']}")
            print(f"Status: {cluster['status']}")
            print(f"Registered container instances: {cluster.get('registeredContainerInstancesCount', 0)}")
            print(f"Running tasks: {cluster.get('runningTasksCount', 0)}")
            print(f"Active services: {cluster.get('activeServicesCount', 0)}")
        else:
            print("Cluster not found")
            
    except Exception as e:
        print(f"Error accessing ECS: {str(e)}")

def main():
    """Run all tests"""
    print("Starting Session Manager tests with real AWS services")
    print(f"Region: {os.environ.get('AWS_REGION')}")
    print(f"Cluster: {os.environ.get('ECS_CLUSTER')}")
    print(f"DynamoDB Table: {os.environ.get('SESSION_TABLE')}")
    
    # Test ECS access first
    test_ecs_access()
    
    # Test DynamoDB access
    test_direct_dynamodb()
    
    # Test Lambda functions
    test_list_sessions()
    
    # Create a session (this might fail if ECS task definition doesn't exist yet)
    # session_id = test_create_session()
    # if session_id:
    #     test_get_session(session_id)

if __name__ == '__main__':
    main()