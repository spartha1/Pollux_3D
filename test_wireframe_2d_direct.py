#!/usr/bin/env python3
"""
Test script to directly test wireframe_2d functionality
"""

import requests
import json
import sys
import os

def test_wireframe_2d():
    """Test wireframe_2d preview generation"""
    
    # Server URL
    server_url = "http://127.0.0.1:8052"
    
    # File path
    file_path = "C:/xampp/htdocs/laravel/Pollux_3D/app/storage/app/uploads/c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL"
    
    # Check if file exists
    if not os.path.exists(file_path.replace('/', '\\')):
        print(f"ERROR: File not found: {file_path}")
        return False
    
    print(f"Testing wireframe_2d with file: {file_path}")
    
    # Test server health first
    try:
        health_response = requests.get(f"{server_url}/health")
        print(f"Server health: {health_response.status_code} - {health_response.json()}")
    except Exception as e:
        print(f"Server health check failed: {e}")
        return False
    
    # Test wireframe_2d generation
    payload = {
        "file_path": file_path,
        "preview_type": "wireframe_2d",
        "width": 800,
        "height": 600,
        "file_id": "42"
    }
    
    try:
        print(f"Sending request: {json.dumps(payload, indent=2)}")
        response = requests.post(f"{server_url}/generate-preview", json=payload)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS! wireframe_2d preview generated:")
            print(f"- Generator: {result.get('generator', 'unknown')}")
            print(f"- Preview filename: {result.get('preview_filename', 'unknown')}")
            print(f"- Success: {result.get('success', False)}")
            print(f"- Final path: {result.get('final_path', 'unknown')}")
            return True
        else:
            print(f"ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing wireframe_2d preview generation...")
    success = test_wireframe_2d()
    sys.exit(0 if success else 1)
