#!/usr/bin/env python3
# ABOUTME: Script to enable CORS on API Gateway endpoints
# ABOUTME: Configures proper CORS headers for browser compatibility

import boto3
import json

client = boto3.client('apigateway', region_name='us-west-2')
api_id = 'p0lkqwkiy4'

def enable_cors_for_resource(resource_id, methods):
    """Enable CORS for a specific resource and methods"""
    
    for method in methods:
        try:
            # First, ensure method response exists
            try:
                client.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': False,
                        'method.response.header.Access-Control-Allow-Headers': False,
                        'method.response.header.Access-Control-Allow-Methods': False
                    }
                )
            except:
                pass  # Method response might already exist
            
            # Add integration response
            try:
                client.put_integration_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        'method.response.header.Access-Control-Allow-Methods': "'GET,POST,DELETE,OPTIONS'"
                    }
                )
            except:
                pass
                
            # For POST, also handle 201
            if method == 'POST':
                try:
                    client.put_method_response(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=method,
                        statusCode='201',
                        responseParameters={
                            'method.response.header.Access-Control-Allow-Origin': False,
                            'method.response.header.Access-Control-Allow-Headers': False,
                            'method.response.header.Access-Control-Allow-Methods': False
                        }
                    )
                    
                    client.put_integration_response(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=method,
                        statusCode='201',
                        responseParameters={
                            'method.response.header.Access-Control-Allow-Origin': "'*'",
                            'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                            'method.response.header.Access-Control-Allow-Methods': "'GET,POST,DELETE,OPTIONS'"
                        }
                    )
                except Exception as e:
                    print(f"Error setting up 201 response for {method}: {e}")
            
            print(f"Enabled CORS for {method} on resource {resource_id}")
            
        except Exception as e:
            print(f"Error enabling CORS for {method}: {e}")

# Get all resources
resources = client.get_resources(restApiId=api_id)

# Find /sessions resource
sessions_resource = None
for resource in resources['items']:
    if resource.get('path') == '/sessions':
        sessions_resource = resource['id']
        print(f"Found /sessions resource: {sessions_resource}")
        break

if sessions_resource:
    # Enable CORS for POST and GET
    enable_cors_for_resource(sessions_resource, ['POST', 'GET'])
    
    # Also enable for OPTIONS
    try:
        # Create OPTIONS method if it doesn't exist
        client.put_method(
            restApiId=api_id,
            resourceId=sessions_resource,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        # Create mock integration
        client.put_integration(
            restApiId=api_id,
            resourceId=sessions_resource,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        # Create method response
        client.put_method_response(
            restApiId=api_id,
            resourceId=sessions_resource,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': False,
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False
            }
        )
        
        # Create integration response
        client.put_integration_response(
            restApiId=api_id,
            resourceId=sessions_resource,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': "'*'",
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,DELETE,OPTIONS'"
            }
        )
        
        print("Created OPTIONS method for CORS preflight")
    except Exception as e:
        print(f"Error creating OPTIONS method: {e}")

# Deploy the API
deployment = client.create_deployment(
    restApiId=api_id,
    stageName='dev',
    description='Enable CORS support'
)

print(f"API deployed with deployment ID: {deployment['id']}")