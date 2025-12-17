"""
Automated reverse image search - handles local images
"""

import requests
import json
import time
from pathlib import Path
from tqdm import tqdm
import yaml
from urllib.parse import quote
from datetime import datetime
import webbrowser
from config.config import GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID

class ReverseImageSearcher:
    """Automate reverse image search"""
    
    def __init__(self, config_path='config/config.yaml'):
        """Load API credentials"""
        
        self.api_key = GOOGLE_API_KEY
        self.engine_id = GOOGLE_SEARCH_ENGINE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.engine_id:
            raise ValueError("❌ Missing API credentials. Check .env file.")
        
        print("✅ API configured")
    
    def search_by_filename(self, image_filename):
        """
        Search using image filename/description
        
        Note: Google Custom Search API doesn't support direct image upload.
        We search by filename/description as proxy.
        """
        
        # Extract meaningful terms from filename
        search_query = self._filename_to_query(image_filename)
        
        params = {
            'key': self.api_key,
            'cx': self.engine_id,
            'q': search_query,
            'searchType': 'image',
            'num': 10
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'items' not in data:
                return []
            
            results = []
            for item in data['items']:
                result = {
                    'page_url': item.get('image', {}).get('contextLink', ''),
                    'image_url': item.get('link', ''),
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'domain': item.get('displayLink', ''),
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"⚠️  Search error: {e}")
            return []
    
    def _filename_to_query(self, filename):
        """Convert filename to search query"""
        # Remove extension and path
        name = Path(filename).stem
        # Add context
        return f"{name} image news"

def hybrid_annotation():
    """
    Hybrid approach:
    1. Auto-search by filename (limited accuracy)
    2. Open manual search for verification
    3. User confirms or adds results
    """
    
    print("=" * 60)
    print("Hybrid Automated Annotation")
    print("=" * 60)
    
    workspace = Path('data/annotations/workspace')
    metadata_file = workspace / 'selected_images.json'
    
    with open(metadata_file) as f:
        images = json.load(f)
    
    # Initialize searcher
    try:
        searcher = ReverseImageSearcher()
    except ValueError as e:
        print(f"{e}")
        return
    
    print(f"\n📋 Annotating {len(images)} images")
    print(f"   Free tier: 100 queries/day")
    print(f"   Strategy: Auto-search + manual verification\n")
    
    annotations = []
    daily_limit = 100
    
    for idx, img_data in enumerate(images[:daily_limit]):
        print(f"\n{'='*60}")
        print(f"Image {idx+1}/{min(daily_limit, len(images))}: {img_data['image_id']}")
        print(f"{'='*60}")
        
        img_path = Path('data/raw') / img_data['img_path']
        
        # Auto-search
        print(f"🔍 Auto-searching...")
        auto_results = searcher.search_by_filename(img_path.name)
        
        if auto_results:
            print(f"✅ Found {len(auto_results)} automated results:")
            for i, result in enumerate(auto_results[:3], 1):
                print(f"   {i}. {result['domain']}: {result['snippet'][:60]}...")
        else:
            print(f"⚠️  No automated results")
        
        # Manual verification
        print(f"\n📸 Opening manual search for verification...")
        manual_url = f"https://www.google.com/searchbyimage?image_url=file:///{img_path.absolute()}"
        print(f"   Manual search: https://images.google.com/")
        print(f"   (Drag-drop: {img_path.absolute()})")
        
        # User input
        print(f"\nCollect 3-5 temporal instances:")
        temporal_sequence = []
        
        for i in range(5):
            print(f"\n  Instance {i+1} (Enter to skip):")
            url = input(f"    URL: ").strip()
            if not url:
                break
            
            caption = input(f"    Caption: ").strip()
            date = input(f"    Date (YYYY-MM-DD): ").strip()
            domain = input(f"    Domain: ").strip()
            
            temporal_sequence.append({
                'url': url,
                'caption': caption,
                'date': date,
                'domain': domain
            })
        
        annotation = {
            'image_id': img_data['image_id'],
            'img_path': str(img_path),
            'reference_caption': img_data['caption1'],
            'temporal_sequence': temporal_sequence,
            'auto_results': auto_results[:3],  # Save for reference
            'annotated_at': datetime.now().isoformat()
        }
        
        annotations.append(annotation)
        
        # Save progress
        if (idx + 1) % 10 == 0:
            progress_file = workspace / 'annotations_progress.json'
            with open(progress_file, 'w') as f:
                json.dump(annotations, f, indent=2)
            print(f"\n💾 Progress saved: {idx+1} completed")
        
        # Rate limit
        time.sleep(1.2)
        
        # Daily limit check
        if idx + 1 >= daily_limit:
            print(f"\n⏸️  Reached daily limit ({daily_limit} queries)")
            print(f"   Continue tomorrow for remaining {len(images) - daily_limit}")
            break
        
        # Continue?
        if idx < min(daily_limit, len(images)) - 1:
            cont = input(f"\nContinue? (y/n): ")
            if cont.lower() != 'y':
                print(f"\n⏸️  Paused at {idx+1}/{len(images)}")
                break
    
    # Final save
    output_file = workspace / 'temporal_annotations.json'
    with open(output_file, 'w') as f:
        json.dump(annotations, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Session complete!")
    print(f"{'='*60}")
    print(f"   Annotated: {len(annotations)}")
    print(f"   Remaining: {len(images) - len(annotations)}")
    print(f"   Saved to: {output_file}")
    
    if len(annotations) < len(images):
        print(f"\nRun again tomorrow to continue (100 more queries)")

if __name__ == "__main__":
    hybrid_annotation()