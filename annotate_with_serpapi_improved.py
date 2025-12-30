"""
Improved annotation with English-only, unique domains, and auto-save
"""
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from serpapi import GoogleSearch
from urllib.parse import quote, urlparse

# Fix Windows encoding
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
        # Remove www. and m. prefixes
        for prefix in ['www.', 'm.']:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        return domain

    def is_english_only(self, url):
        """Check if URL is English-language only"""
        # Non-English patterns in URLs
        non_english = [
            '/ar/', '/zh/', '/cn/', '/es/', '/fr/', '/de/', '/pt/', '/ru/',
            '/ja/', '/ko/', '/it/', '/tr/', '/pl/', '/nl/', '/sv/', '/id/',
            '/th/', '/vi/', '/fa/', '/hi/', '/bn/', '/ur/', '/sw/', '/ara/',
            'gahuza', 'kirundi', 'kinyarwanda',  # African languages
            '/amharic/', '/hausa/', '/somali/', '/afaan/',
        ]

        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in non_english)

    def reverse_image_search(self, image_filename, max_results=20):
        """
        Search with strict filtering:
        - English only
        - Unique domains
        - Exact matches preferred
        """
        image_url = f"{self.ngrok_url}/images/{quote(image_filename)}"

        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": self.api_key,
            "hl": "en"  # English only
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            if 'error' in results:
                error_msg = results.get('error', 'Unknown error')
                print(f"  ⚠️  API Error: {error_msg}")

                # Check if rate limit
                if 'limit' in error_msg.lower() or 'quota' in error_msg.lower():
                    print(f"  🛑 API LIMIT REACHED - Stopping annotation")
                    return None  # Signal to stop

                return []

            # Prioritize exact matches over similar
            exact_matches = results.get("image_results", [])
            visual_matches = results.get("visual_matches", [])

            all_matches = exact_matches + visual_matches

            # Filter with strict criteria
            seen_domains = set()
            filtered = []

            # Skip image hosts and aggregators
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

                # Filter 1: English only
                if not self.is_english_only(url):
                    continue

                # Filter 2: Skip image hosts
                if any(skip in url.lower() for skip in skip_domains):
                    continue

                # Filter 3: Unique domains only
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

    def annotate_images(self, image_dir, output_file, max_images=245, save_every=10):
        """
        Annotate with auto-save every N images

        Args:
            save_every: Save progress every N images (default: 10)
        """
        image_dir = Path(image_dir)
        image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
        image_files = image_files[:max_images]

        print("=" * 80)
        print(f"IMPROVED ANNOTATION - English Only + Unique Domains")
        print("=" * 80)
        print(f"Images to process: {len(image_files)}")
        print(f"Using ngrok URL: {self.ngrok_url}")
        print(f"Output: {output_file}")
        print(f"Auto-save every: {save_every} images")
        print(f"Filters: English only, unique domains, no image hosts")
        print("=" * 80)
        print()

        results = []
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing results if resuming
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            print(f"📂 Loaded {len(results)} existing results")
            print()

        for i, img_path in enumerate(image_files, 1):
            print(f"[{i}/{len(image_files)}] {img_path.name}")
            print("-" * 80)

            # Search
            matches = self.reverse_image_search(img_path.name, max_results=20)

            # Check if API limit reached
            if matches is None:
                print()
                print("=" * 80)
                print("🛑 API LIMIT REACHED")
                print("=" * 80)
                print(f"Processed: {i-1} images")
                print(f"Saving results...")
                break

            # Count results
            english_count = len(matches)
            print(f"  ✅ Found {english_count} English results (unique domains)")

            if matches:
                print(f"  Top 5:")
                for j, match in enumerate(matches[:5], 1):
                    print(f"    {j}. [{match['domain']}] {match['title'][:50]}...")

            results.append({
                'image_id': img_path.stem,
                'filename': img_path.name,
                'match_count': english_count,
                'matches': matches
            })

            # Auto-save every N images
            if i % save_every == 0:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"  💾 Progress saved ({i} images)")

            # Rate limiting
            if i < len(image_files):
                print(f"  ⏳ Waiting 2 seconds...")
                time.sleep(2)

            print()

        # Final save
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print("=" * 80)
        print("✅ Annotation Complete!")
        print("=" * 80)
        print(f"Total processed: {len(results)} images")
        print(f"Saved to: {output_path}")

        # Statistics
        total_matches = sum(r['match_count'] for r in results)
        avg_matches = total_matches / len(results) if results else 0
        print(f"Total matches: {total_matches}")
        print(f"Average per image: {avg_matches:.1f}")
        print("=" * 80)


def main():
    print()
    print("⚠️  IMPORTANT: Make sure Flask and ngrok are running!")
    print()

    ngrok_url = input("Enter your ngrok URL: ").strip()

    if not ngrok_url.startswith('http'):
        print("❌ Invalid URL")
        return

    print()
    print("📊 SerpAPI Usage:")
    print(f"   Remaining searches: ~245")
    print(f"   Recommendation: Process 200-240 images to stay safe")
    print()

    max_images = input("How many images to process? (default: 240): ").strip()
    max_images = int(max_images) if max_images else 240

    print()
    confirm = input(f"Process {max_images} images? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Cancelled.")
        return

    # Initialize
    annotator = ImprovedAnnotator(ngrok_url)

    # Process
    image_dir = "data/annotations/workspace/images_to_annotate"
    output_file = "data/annotations/serpapi_results_filtered.json"

    annotator.annotate_images(
        image_dir=image_dir,
        output_file=output_file,
        max_images=max_images,
        save_every=10  # Save every 10 images
    )

if __name__ == "__main__":
    main()
