#!/usr/bin/env python3
# ABOUTME: Script to generate API keys for testing
# ABOUTME: Creates API keys directly in DynamoDB

import boto3
import uuid
import hashlib
import json
import argparse
import time

def generate_api_key(user_id: str, tier: str = 'basic'):
    """Generate a new API key"""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('computer-use-api-keys-dev')
    
    # Generate secure API key
    raw_key = f"{user_id}:{uuid.uuid4()}:{time.time()}"
    api_key = hashlib.sha256(raw_key.encode()).hexdigest()
    
    # Set rate limits based on tier
    rate_limits = {
        'basic': 1000,      # 1000 requests per day
        'standard': 10000,  # 10k requests per day
        'premium': 100000   # 100k requests per day
    }
    
    # Create key entry
    key_data = {
        'api_key': api_key,
        'key_id': str(uuid.uuid4()),
        'user_id': user_id,
        'tier': tier,
        'rate_limit': rate_limits.get(tier, 1000),
        'usage_count': 0,
        'active': True,
        'created_at': int(time.time()),
        'expires_at': int(time.time()) + 365 * 24 * 60 * 60  # 1 year
    }
    
    # Store in DynamoDB
    table.put_item(Item=key_data)
    
    return api_key, key_data

def main():
    parser = argparse.ArgumentParser(description='Generate API keys for Computer Use Demo')
    parser.add_argument('--user-id', default='test-user', help='User ID for the API key')
    parser.add_argument('--tier', default='basic', choices=['basic', 'standard', 'premium'], 
                        help='API tier (basic, standard, premium)')
    parser.add_argument('--count', type=int, default=1, help='Number of keys to generate')
    
    args = parser.parse_args()
    
    print(f"Generating {args.count} API key(s) for user '{args.user_id}' with tier '{args.tier}'...")
    
    for i in range(args.count):
        user_id = args.user_id
        if args.count > 1:
            user_id = f"{args.user_id}-{i+1}"
        
        try:
            api_key, key_data = generate_api_key(user_id, args.tier)
            
            print(f"\nAPI Key #{i+1} created successfully!")
            print(f"User ID: {user_id}")
            print(f"API Key: {api_key}")
            print(f"Tier: {args.tier}")
            print(f"Rate Limit: {key_data['rate_limit']} requests/day")
            print("\n⚠️  Store this API key securely. It cannot be retrieved again.")
            
            # Save to file
            with open(f'api-key-{user_id}.txt', 'w') as f:
                f.write(f"API_KEY={api_key}\n")
                f.write(f"USER_ID={user_id}\n")
                f.write(f"TIER={args.tier}\n")
            
            print(f"API key saved to: api-key-{user_id}.txt")
            
        except Exception as e:
            print(f"Error generating API key: {e}")
    
    print("\n✅ API key generation complete!")
    print("\nTo use the API key, add it to your request headers:")
    print("Authorization: Bearer <your-api-key>")

if __name__ == "__main__":
    main()