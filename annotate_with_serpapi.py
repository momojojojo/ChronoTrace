"""
Automated annotation using SerpAPI + Flask + ngrok
"""
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from serpapi import GoogleSearch
from urllib.parse import quote

# Fix Windows encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_KEY:
    raise RuntimeError("SERPAPI_KEY missing from .env")

class SerpAPIAnnotator:
    def __init__(self, ngrok_url):
        """
        Args:
            ngrok_url: Your ngrok public URL (e.g., https://abc123.ngrok.io)
        """
        self.ngrok_url = ngrok_url.rstrip('/')
        self.api_key = SERPAPI_KEY

    def reverse_image_search(self, image_filename, max_results=20):
        """
        Search for image using SerpAPI Google Lens

        Args:
            image_filename: Just the filename (e.g., "1.jpg")
            max_results: Max number of results to return

        Returns:
            List of dicts with URL matches
        """
        # Build public URL
        image_url = f"{self.ngrok_url}/images/{quote(image_filename)}"

        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": self.api_key,
            "hl": "en"
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            if 'error' in results:
                print(f"  ⚠️  API Error: {results['error']}")
                return []

            visual_matches = results.get("visual_matches", [])

            matches = []
            for match in visual_matches[:max_results]:
                matches.append({
                    'url': match.get('link', ''),
                    'title': match.get('title', ''),
                    'source': match.get('source', ''),
                    'thumbnail': match.get('thumbnail', '')
                })

            return matches

        except Exception as e:
            print(f"  ⚠️  Search error: {e}")
            return []

    def annotate_images(self, image_dir, output_file, max_images=1):
        """
        Annotate a batch of images

        Args:
            image_dir: Directory containing images
            output_file: Where to save results
            max_images: Max number of images to process
        """
        image_dir = Path(image_dir)
        image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
        image_files = image_files[:max_images]

        print("=" * 60)
        print(f"SerpAPI Annotation via ngrok")
        print("=" * 60)
        print(f"Images to process: {len(image_files)}")
        print(f"Using ngrok URL: {self.ngrok_url}")
        print(f"Output: {output_file}")
        print("=" * 60)
        print()

        results = []

        for i, img_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] {img_path.name}")
            print("-" * 60)

            # Search
            matches = self.reverse_image_search(img_path.name)

            print(f"  ✅ Found {len(matches)} visual matches")

            if matches:
                print(f"  Top 3 results:")
                for j, match in enumerate(matches[:3], 1):
                    print(f"    {j}. {match['title'][:60]}...")
                    print(f"       {match['url']}")

            results.append({
                'image_id': img_path.stem,
                'filename': img_path.name,
                'match_count': len(matches),
                'matches': matches
            })

            # Rate limiting - be nice to the API
            if i < len(image_files):
                print(f"  ⏳ Waiting 2 seconds...")
                time.sleep(2)

        # Save results
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print()
        print("=" * 60)
        print("✅ Annotation Complete!")
        print("=" * 60)
        print(f"Processed: {len(results)} images")
        print(f"Saved to: {output_path}")

        # Statistics
        total_matches = sum(r['match_count'] for r in results)
        avg_matches = total_matches / len(results) if results else 0
        print(f"Total matches: {total_matches}")
        print(f"Average per image: {avg_matches:.1f}")
        print("=" * 60)


def main():
    """Main execution"""
    print()
    print("⚠️  IMPORTANT: Before running this script:")
    print()
    print("1. Start the Flask server:")
    print("   python image_server.py")
    print()
    print("2. In another terminal, start ngrok:")
    print("   ngrok http 5000")
    print()
    print("3. Copy the ngrok HTTPS URL (e.g., https://abc123.ngrok-free.app)")
    print()

    ngrok_url = input("Enter your ngrok URL: ").strip()

    if not ngrok_url.startswith('http'):
        print("❌ Invalid URL. Must start with https://")
        return

    print()
    confirm = input(f"Using ngrok URL: {ngrok_url}\nContinue? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Cancelled.")
        return

    # Initialize annotator
    annotator = SerpAPIAnnotator(ngrok_url)

    # Process images
    image_dir = "data/annotations/workspace/images_to_annotate"
    output_file = "data/annotations/serpapi_results.json"

    # Start with a small batch for testing
    max_images = 1

    print()
    print(f"Processing {max_images} images (test batch)...")
    print()

    annotator.annotate_images(
        image_dir=image_dir,
        output_file=output_file,
        max_images=max_images
    )

if __name__ == "__main__":
    main()
