# ABOUTME: Health check script for VNC bridge container
# ABOUTME: Validates that the FastAPI service is responding correctly

#!/usr/bin/env python3
import sys
import urllib.request
import urllib.error
import json

def check_health():
    """Check if the VNC bridge service is healthy"""
    try:
        # Try to connect to the health endpoint
        response = urllib.request.urlopen('http://localhost:8080/health', timeout=5)
        data = json.loads(response.read().decode())
        
        # Check if status is healthy
        if data.get('status') == 'healthy':
            print("Health check passed")
            return 0
        else:
            print(f"Health check failed: {data}")
            return 1
            
    except urllib.error.URLError as e:
        print(f"Connection error: {e}")
        return 1
    except Exception as e:
        print(f"Health check error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())