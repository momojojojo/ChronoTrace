"""
Compare old vs new filtering results
"""
import json
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def compare_results():
    old_file = Path("data/annotations/serpapi_results.json")
    new_file = Path("data/annotations/serpapi_results_filtered.json")

    if not old_file.exists():
        print("❌ Old results not found")
        return

    with open(old_file, 'r', encoding='utf-8') as f:
        old_results = json.load(f)[0]  # First image

    print("=" * 80)
    print("COMPARISON: Old vs New Filtering")
    print("=" * 80)
    print()

    print(f"OLD RESULTS (image: {old_results['filename']})")
    print(f"Total matches: {old_results['match_count']}")
    print("-" * 80)

    # Count domains
    domains_old = {}
    for match in old_results['matches']:
        source = match.get('source', 'Unknown')
        domains_old[source] = domains_old.get(source, 0) + 1

    print("\nDomain distribution:")
    for domain, count in sorted(domains_old.items(), key=lambda x: x[1], reverse=True):
        print(f"  {domain}: {count}")

    print("\nTop 5 URLs:")
    for i, match in enumerate(old_results['matches'][:5], 1):
        english = '✅' if '/ar/' not in match['url'] and '/gahuza/' not in match['url'] else '❌'
        print(f"  {i}. {english} {match['url']}")

    print("\n" + "=" * 80)
    print("ISSUES IDENTIFIED:")
    print("=" * 80)
    print(f"❌ Duplicate domains: BBC appears {domains_old.get('BBC', 0)} times")
    print(f"❌ Non-English: Link 2 is Kinyarwanda (/gahuza/)")
    print(f"❌ Non-English: Link 5 is Arabic (/ara/)")
    print()
    print("=" * 80)
    print("NEW FILTERING WILL:")
    print("=" * 80)
    print("✅ Keep only 1 result per domain (BBC, Facebook, etc.)")
    print("✅ Remove non-English URLs (/gahuza/, /ara/, etc.)")
    print("✅ Remove image hosts (Pinterest, Getty, etc.)")
    print("✅ Prioritize exact matches over similar")
    print("=" * 80)

if __name__ == "__main__":
    compare_results()
