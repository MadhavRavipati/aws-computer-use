import boto3
import zipfile
import os

# Download current function
lambda_client = boto3.client('lambda', region_name='us-west-2')
s3 = boto3.client('s3', region_name='us-west-2')

# Get function
response = lambda_client.get_function(FunctionName='computer-use-session-manager-dev')
code_location = response['Code']['Location']

# Download zip
import urllib.request
urllib.request.urlretrieve(code_location, 'current_function.zip')

# Extract
with zipfile.ZipFile('current_function.zip', 'r') as zip_ref:
    zip_ref.extractall('temp_lambda')

# Read the session_manager.py
with open('temp_lambda/session_manager.py', 'r') as f:
    content = f.read()

# Add CORS headers to all return statements
cors_headers = """'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },"""

# Update return statements
content = content.replace(
    "'statusCode': 200,\n            'body':",
    f"'statusCode': 200,\n            {cors_headers}\n            'body':"
)
content = content.replace(
    "'statusCode': 404,\n                'body':",
    f"'statusCode': 404,\n                {cors_headers}\n                'body':"
)
content = content.replace(
    "'statusCode': 500,\n            'body':",
    f"'statusCode': 500,\n            {cors_headers}\n            'body':"
)

# Write updated file
with open('temp_lambda/session_manager.py', 'w') as f:
    f.write(content)

# Create new zip
with zipfile.ZipFile('updated_function.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('temp_lambda'):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, 'temp_lambda')
            zipf.write(file_path, arcname)

print("Function package updated with CORS headers")

# Clean up
import shutil
shutil.rmtree('temp_lambda')
os.remove('current_function.zip')
