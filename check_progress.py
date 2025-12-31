"""
Check annotation progress and statistics
"""
import json
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_progress():
    results_file = Path('data/annotations/serpapi_results_filtered.json')

    if not results_file.exists():
        print("❌ No results file found")
        print("   Run: python annotate_with_serpapi_improved.py")
        return

    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    total_images = 500  # Total in workspace
    processed = len(results)
    remaining = total_images - processed

    print("=" * 80)
    print("ANNOTATION PROGRESS")
    print("=" * 80)
    print()

    # Progress bar
    progress_pct = (processed / total_images) * 100
    bar_length = 50
    filled = int(bar_length * processed / total_images)
    bar = '█' * filled + '░' * (bar_length - filled)

    print(f"Progress: [{bar}] {progress_pct:.1f}%")
    print()
    print(f"✅ Processed:  {processed} images")
    print(f"⏳ Remaining:  {remaining} images")
    print(f"📊 Total:      {total_images} images")
    print()

    # Statistics
    total_matches = sum(r['match_count'] for r in results)
    avg_matches = total_matches / processed if processed else 0

    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)
    print(f"Total URLs found:     {total_matches}")
    print(f"Average per image:    {avg_matches:.1f}")
    print()

    # Domain breakdown
    all_domains = {}
    for result in results:
        for match in result['matches']:
            domain = match.get('domain', 'Unknown')
            all_domains[domain] = all_domains.get(domain, 0) + 1

    print(f"Unique domains:       {len(all_domains)}")
    print()
    print("Top 10 domains:")
    for domain, count in sorted(all_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {domain}: {count}")

    print()
    print("=" * 80)
    print("RECENT IMAGES")
    print("=" * 80)

    last_5 = results[-5:]
    for r in last_5:
        print(f"  {r['filename']}: {r['match_count']} matches")

    print()
    print("=" * 80)

    if remaining > 0:
        print("TO RESUME:")
        print("  python resume_annotation.py")
    else:
        print("✅ ALL IMAGES ANNOTATED!")

    print("=" * 80)

if __name__ == "__main__":
    check_progress()
