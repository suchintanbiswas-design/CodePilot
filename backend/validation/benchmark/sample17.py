import os
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# Application settings
UPLOAD_DIR = "/var/www/uploads/"
ALLOWED_HOSTS = ["api.internal.network", "proxy.internal.network"]

@app.route('/api/v1/fetch_image', methods=['POST'])
def fetch_remote_image():
    """
    Fetches an image from a user-provided URL and stores it.
    """
    data = request.get_json()
    if not data or 'image_url' not in data:
        return jsonify({"error": "Missing image_url"}), 400
        
    image_url = data['image_url']
    
    # Critical security: SSRF (Server-Side Request Forgery)
    # The application makes an outbound request to an untrusted URL
    # without validating the domain against an allowlist.
    try:
        response = requests.get(image_url, timeout=10)
        
        if response.status_code == 200:
            filename = image_url.split('/')[-1]
            if not filename:
                filename = "default.jpg"
                
            save_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
                
            return jsonify({"status": "success", "file": filename})
        else:
            return jsonify({"error": "Failed to fetch image"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/download', methods=['GET'])
def download_file():
    """
    Downloads a previously fetched image.
    """
    filename = request.args.get('file')
    if not filename:
        return jsonify({"error": "Missing file parameter"}), 400
        
    # Critical security: Path Traversal
    # The application concatenates untrusted input directly into a file path
    # without sanitizing for directory traversal sequences (e.g., ../)
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

def initialize_directories():
    """
    Ensure required directories exist.
    """
    if not os.path.exists(UPLOAD_DIR):
        try:
            os.makedirs(UPLOAD_DIR)
        except OSError:
            pass

if __name__ == '__main__':
    initialize_directories()
    app.run(host='0.0.0.0', port=8000)
