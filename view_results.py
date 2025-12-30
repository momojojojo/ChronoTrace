"""
View annotation results in a readable format
"""
import json
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def view_results(json_file='data/annotations/serpapi_results.json'):
    """Display results in readable format"""

    json_path = Path(json_file)

    if not json_path.exists():
        print(f"❌ Results file not found: {json_path}")
        print(f"\nRun annotation first:")
        print(f"  python annotate_with_serpapi.py")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print("=" * 80)
    print(f"ANNOTATION RESULTS: {len(results)} images")
    print("=" * 80)
    print()

    for result in results:
        print(f"{'='*80}")
        print(f"IMAGE: {result['filename']} (ID: {result['image_id']})")
        print(f"{'='*80}")
        print(f"Total matches found: {result['match_count']}")
        print()

        matches = result['matches']

        if matches:
            print(f"Top {min(10, len(matches))} Results:")
            print("-" * 80)

            for i, match in enumerate(matches[:10], 1):
                print(f"\n{i}. {match['title'][:70]}")
                print(f"   Source: {match['source']}")
                print(f"   URL: {match['url']}")
        else:
            print("⚠️  No matches found")

        print()
        print("=" * 80)
        print()

if __name__ == "__main__":
    view_results()
