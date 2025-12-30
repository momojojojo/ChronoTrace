"""
Quick test: ngrok + SerpAPI reverse image search
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_KEY:
    raise RuntimeError("SERPAPI_KEY missing from .env")

def test_reverse_search(ngrok_url, image_filename):
    """Test reverse image search with ngrok URL"""

    # Build full URL
    image_url = f"{ngrok_url}/images/{image_filename}"

    print("=" * 60)
    print("Testing SerpAPI Google Lens with ngrok")
    print("=" * 60)
    print(f"ngrok URL: {ngrok_url}")
    print(f"Image: {image_filename}")
    print(f"Full URL: {image_url}")
    print("=" * 60)
    print()

    # Make request
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": SERPAPI_KEY,
        "hl": "en"
    }

    print("Sending request to SerpAPI...")

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # Check for errors
        if 'error' in results:
            print(f"❌ ERROR: {results['error']}")
            return False

        # Get visual matches
        visual_matches = results.get("visual_matches", [])

        print(f"✅ SUCCESS!")
        print(f"Found {len(visual_matches)} visual matches")
        print()

        if visual_matches:
            print("Top 5 results:")
            print("-" * 60)
            for i, match in enumerate(visual_matches[:5], 1):
                title = match.get('title', 'No title')
                link = match.get('link', 'No link')
                source = match.get('source', 'Unknown')

                print(f"{i}. {title[:70]}")
                print(f"   Source: {source}")
                print(f"   URL: {link}")
                print()
        else:
            print("⚠️  No visual matches found")

        return True

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print()
    print("🔧 Quick Test: ngrok + SerpAPI")
    print()
    print("Before running this:")
    print("1. Start Flask server: python image_server.py")
    print("2. Start ngrok: ngrok http 5000")
    print()

    ngrok_url = input("Enter your ngrok HTTPS URL: ").strip()

    if not ngrok_url.startswith('http'):
        print("❌ Invalid URL. Must start with https://")
        sys.exit(1)

    print()

    # Test with first available image
    images_dir = Path("data/annotations/workspace/images_to_annotate")
    test_image = None

    for ext in ['.jpg', '.png', '.jpeg']:
        images = list(images_dir.glob(f"*{ext}"))
        if images:
            test_image = images[0].name
            break

    if not test_image:
        print("❌ No test images found")
        sys.exit(1)

    print(f"Using test image: {test_image}")
    print()

    # Run test
    success = test_reverse_search(ngrok_url, test_image)

    print()
    print("=" * 60)
    if success:
        print("✅ TEST PASSED - Ready to run full annotation!")
        print()
        print("Next step:")
        print("  python annotate_with_serpapi.py")
    else:
        print("❌ TEST FAILED - Check the error above")
    print("=" * 60)
