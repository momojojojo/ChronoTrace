"""
Convert JSON results to CSV format for review
"""
import json
import csv
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def convert_to_csv():
    json_file = Path('data/annotations/serpapi_results_filtered.json')
    csv_file = Path('data/annotations/serpapi_results.csv')

    if not json_file.exists():
        print("❌ JSON file not found")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print(f"Converting {len(results)} images to CSV...")

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'image_id',
            'filename',
            'total_matches',
            'url_1', 'title_1', 'domain_1',
            'url_2', 'title_2', 'domain_2',
            'url_3', 'title_3', 'domain_3',
            'url_4', 'title_4', 'domain_4',
            'url_5', 'title_5', 'domain_5',
        ])

        # Data rows
        for result in results:
            row = [
                result['image_id'],
                result['filename'],
                result['match_count']
            ]

            # Add up to 5 matches
            matches = result['matches'][:5]
            for match in matches:
                row.extend([
                    match['url'],
                    match['title'],
                    match['domain']
                ])

            # Pad if less than 5 matches
            while len(row) < 18:  # 3 + 5*3
                row.extend(['', '', ''])

            writer.writerow(row)

    print(f"✅ Saved to: {csv_file}")
    print(f"   {len(results)} images")
    print(f"   Open in Excel or Google Sheets")

if __name__ == "__main__":
    convert_to_csv()
