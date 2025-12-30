"""
Simple Flask server to serve local images via ngrok
"""
from flask import Flask, send_from_directory
from pathlib import Path

app = Flask(__name__)

# Path to your images
IMAGES_DIR = Path("data/annotations/workspace/images_to_annotate")

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve image from local directory"""
    return send_from_directory(IMAGES_DIR, filename)

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "ok", "images_dir": str(IMAGES_DIR.absolute())}

if __name__ == '__main__':
    print("=" * 60)
    print("Image Server Running")
    print("=" * 60)
    print(f"Serving images from: {IMAGES_DIR.absolute()}")
    print()
    print("Next steps:")
    print("1. Run this server")
    print("2. In another terminal, run: ngrok http 5000")
    print("3. Copy the ngrok HTTPS URL")
    print("4. Run your annotation script with that URL")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False)
