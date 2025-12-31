"""
Resume annotation from where it stopped - no duplicates
"""
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from serpapi import GoogleSearch
from urllib.parse import quote, urlparse

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_KEY:
    raise RuntimeError("SERPAPI_KEY missing from .env")

class ImprovedAnnotator:
    def __init__(self, ngrok_url):
        self.ngrok_url = ngrok_url.rstrip('/')
        self.api_key = SERPAPI_KEY

    def get_domain(self, url):
        """Extract clean domain from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        for prefix in ['www.', 'm.']:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        return domain

    def is_english_only(self, url):
        """Check if URL is English-language only"""
        non_english = [
            '/ar/', '/zh/', '/cn/', '/es/', '/fr/', '/de/', '/pt/', '/ru/',
            '/ja/', '/ko/', '/it/', '/tr/', '/pl/', '/nl/', '/sv/', '/id/',
            '/th/', '/vi/', '/fa/', '/hi/', '/bn/', '/ur/', '/sw/', '/ara/',
            'gahuza', 'kirundi', 'kinyarwanda',
            '/amharic/', '/hausa/', '/somali/', '/afaan/',
        ]
        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in non_english)

    def reverse_image_search(self, image_filename, max_results=20):
        """Search with strict filtering"""
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
                error_msg = results.get('error', 'Unknown error')
                print(f"  ⚠️  API Error: {error_msg}")
                if 'limit' in error_msg.lower() or 'quota' in error_msg.lower():
                    return None
                return []

            exact_matches = results.get("image_results", [])
            visual_matches = results.get("visual_matches", [])
            all_matches = exact_matches + visual_matches

            seen_domains = set()
            filtered = []

            skip_domains = [
                'pinterest', 'gettyimages', 'shutterstock', 'alamy',
                'istockphoto', 'dreamstime', '123rf', 'depositphotos',
                'flickr', 'imgur', 'photobucket'
            ]

            for match in all_matches:
                url = match.get('link', '')
                title = match.get('title', '')
                source = match.get('source', '')

                if not url or not title:
                    continue

                if not self.is_english_only(url):
                    continue

                if any(skip in url.lower() for skip in skip_domains):
                    continue

                domain = self.get_domain(url)
                if domain in seen_domains:
                    continue

                seen_domains.add(domain)
                filtered.append({
                    'url': url,
                    'title': title,
                    'source': source,
                    'domain': domain,
                    'thumbnail': match.get('thumbnail', '')
                })

                if len(filtered) >= max_results:
                    break

            return filtered

        except Exception as e:
            print(f"  ⚠️  Search error: {e}")
            return []

    def resume_annotation(self, image_dir, output_file, max_new_images=185, save_every=10):
        """Resume from existing results - skip already processed"""

        image_dir = Path(image_dir)
        output_path = Path(output_file)

        # Load existing results
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
            processed_filenames = {r['filename'] for r in existing_results}
        else:
            existing_results = []
            processed_filenames = set()

        # Get all images
        all_images = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))

        # Filter out already processed
        remaining_images = [img for img in all_images if img.name not in processed_filenames]
        remaining_images = remaining_images[:max_new_images]

        print("=" * 80)
        print("RESUME ANNOTATION")
        print("=" * 80)
        print(f"Already processed: {len(existing_results)} images")
        print(f"Remaining in folder: {len(remaining_images)} images")
        print(f"Will process: {min(len(remaining_images), max_new_images)} images")
        print(f"Output: {output_file}")
        print("=" * 80)
        print()

        if not remaining_images:
            print("✅ All images already processed!")
            return

        results = existing_results.copy()
        start_count = len(results)

        for i, img_path in enumerate(remaining_images, 1):
            total_count = start_count + i

            print(f"[{i}/{len(remaining_images)}] (Total: {total_count}) {img_path.name}")
            print("-" * 80)

            matches = self.reverse_image_search(img_path.name, max_results=20)

            if matches is None:
                print()
                print("=" * 80)
                print("🛑 API LIMIT REACHED")
                print("=" * 80)
                print(f"New images processed: {i-1}")
                print(f"Total images: {total_count - 1}")
                break

            english_count = len(matches)
            print(f"  ✅ Found {english_count} English results (unique domains)")

            if matches:
                print(f"  Top 3:")
                for j, match in enumerate(matches[:3], 1):
                    print(f"    {j}. [{match['domain']}] {match['title'][:45]}...")

            results.append({
                'image_id': img_path.stem,
                'filename': img_path.name,
                'match_count': english_count,
                'matches': matches
            })

            # Auto-save
            if i % save_every == 0:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"  💾 Saved ({total_count} total images)")

            if i < len(remaining_images):
                print(f"  ⏳ Waiting 2 seconds...")
                time.sleep(2)

            print()

        # Final save
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print("=" * 80)
        print("✅ Session Complete!")
        print("=" * 80)
        print(f"Started with: {start_count} images")
        print(f"Newly processed: {len(results) - start_count} images")
        print(f"Total now: {len(results)} images")
        print(f"Remaining: {500 - len(results)} images")
        print(f"Saved to: {output_path}")
        print("=" * 80)


def main():
    print()
    print("📊 CURRENT STATUS:")

    output_file = "data/annotations/serpapi_results_filtered.json"
    output_path = Path(output_file)

    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f"   Already processed: {len(existing)} images")
        print(f"   Remaining to annotate: {500 - len(existing)} images")
    else:
        print("   No existing results found")

    print()
    print("⚠️  Make sure Flask and ngrok are running!")
    print()

    ngrok_url = input("Enter your ngrok URL: ").strip()

    if not ngrok_url.startswith('http'):
        print("❌ Invalid URL")
        return

    print()
    print("📊 API Usage:")
    print(f"   You used ~60 searches already")
    print(f"   Estimated remaining: ~185 searches")
    print()

    max_images = input("How many MORE images to process? (default: 185): ").strip()
    max_images = int(max_images) if max_images else 185

    print()
    confirm = input(f"Process {max_images} more images? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Cancelled.")
        return

    annotator = ImprovedAnnotator(ngrok_url)

    annotator.resume_annotation(
        image_dir="data/annotations/workspace/images_to_annotate",
        output_file=output_file,
        max_new_images=max_images,
        save_every=10
    )

if __name__ == "__main__":
    main()
