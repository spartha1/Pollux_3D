#!/usr/bin/env python3
import requests
import json
import base64
from PIL import Image
import io
import sys

def test_preview_service(file_path, render_type='3d'):
    print("Testing preview service...")

    # Prepare request
    url = 'http://127.0.0.1:8088/preview'
    data = {
        'file_id': 'test',
        'file_path': file_path,
        'render_type': render_type
    }

    try:
        # Send request
        print(f"Sending request to {url}...")
        response = requests.post(url, json=data)
        response.raise_for_status()

        # Get response data
        print("Processing response...")
        result = response.json()

        if 'image_data' not in result:
            print("Error: No image data in response")
            return False

        # Decode and save image
        print("Saving image...")
        image_data = base64.b64decode(result['image_data'])
        image = Image.open(io.BytesIO(image_data))

        output_file = 'preview_test.png'
        image.save(output_file)
        print(f"Image saved as: {output_file}")

        # Show image
        print("Opening image...")
        image.show()

        return True

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Use test.step from the tests directory
    file_path = 'c:/xampp/htdocs/laravel/PolluxwWeb/tests/test.step'
    test_preview_service(file_path)
