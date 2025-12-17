"""
Quick test of Cloud Vision API
"""

from google.cloud import vision
import os
from pathlib import Path

# Point to your service account key
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'config/notional-sign-481506-r3-57f0e65bf093.json'

# Check if key file exists
key_file = Path('config/notional-sign-481506-r3-57f0e65bf093.json')
if not key_file.exists():
    print("❌ Key file not found!")
    print("   Expected at: config/notional-sign-481506-r3-57f0e65bf093.json")
    exit(1)

print("✅ Key file found")

# Try to initialize client
try:
    client = vision.ImageAnnotatorClient()
    print("✅ Vision API client initialized")
    
    # Test with actual image
    test_img = Path('data/raw/test/1102.jpg')
    if test_img.exists():
        print(f"\n🔍 Testing reverse search on: {test_img.name}")
        
        with open(test_img, 'rb') as f:
            content = f.read()
        
        image = vision.Image(content=content)
        response = client.web_detection(image=image)
        
        matches = response.web_detection.pages_with_matching_images
        
        if matches:
            print(f"✅ Found {len(matches)} pages using this image!")
            print(f"\n🎉 SUCCESS! Vision API is working!")
            print(f"\nFirst 3 URLs:")
            for i, page in enumerate(matches[:3], 1):
                print(f"  {i}. {page.url}")
        else:
            print("⚠️  API works but no matches for this image")
    else:
        print("⚠️  Test image not found, but client initialized OK")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nCommon issues:")
    print("1. Vision API not enabled")
    print("2. Key file in wrong location")
    print("3. Service account doesn't have Vision API permissions")