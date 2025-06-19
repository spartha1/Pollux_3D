import requests
import base64
from PIL import Image
import io
import json

print("Making request to preview server...")
response = requests.post(
    'http://127.0.0.1:8088/preview',
    json={
        'file_id': 'test',
        'file_path': 'c:/xampp/htdocs/laravel/PolluxwWeb/tests/test.step',
        'render_type': '3d'
    }
)

if response.status_code == 200:
    print("Request successful, processing image...")
    data = response.json()
    image_data = base64.b64decode(data['image_data'])

    # Save the image
    image = Image.open(io.BytesIO(image_data))
    output_file = 'preview_test.png'
    image.save(output_file)
    print(f"Image saved as {output_file}")

    # Display the image
    image.show()
else:
    print(f"Error: Server returned status code {response.status_code}")
    print(response.text)

input("Press Enter to exit...")
