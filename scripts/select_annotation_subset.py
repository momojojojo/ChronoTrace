"""
Select 500 diverse images from test set for manual temporal annotation
"""

import json
import random
import shutil
from pathlib import Path
from collections import defaultdict
import sys
sys.path.append('.')

from chronotrace.data.cosmos_loader import COSMOSDataset

def select_500_images():
    """Select 500 diverse images for annotation"""
    
    print("=" * 60)
    print("Selecting 500 Images for Temporal Annotation")
    print("=" * 60)
    
    # Load test dataset
    dataset = COSMOSDataset(split='test', load_images=False)
    
    # Group by caption characteristics
    by_length = defaultdict(list)
    
    for idx, ann in enumerate(dataset.annotations):
        caption1 = ann['caption1']
        caption2 = ann['caption2']
        
        avg_length = (len(caption1.split()) + len(caption2.split())) / 2
        
        if avg_length < 15:
            category = 'short'
        elif avg_length < 30:
            category = 'medium'
        else:
            category = 'long'
        
        by_length[category].append((idx, ann))
    
    print(f"\nCaption length distribution:")
    for cat, items in by_length.items():
        print(f"   {cat}: {len(items)} samples")
    
    # Sample proportionally
    selected = []
    samples_per_category = 500 // len(by_length)
    
    random.seed(42)
    
    for category, items in by_length.items():
        sample_size = min(samples_per_category, len(items))
        sampled = random.sample(items, sample_size)
        selected.extend(sampled)
    
    # Fill remaining slots
    remaining = 500 - len(selected)
    if remaining > 0:
        all_remaining = [(idx, ann) for cat_items in by_length.values() 
                        for idx, ann in cat_items if (idx, ann) not in selected]
        selected.extend(random.sample(all_remaining, remaining))
    
    selected = selected[:500]
    
    print(f"\n✅ Selected {len(selected)} images")
    
    # Create annotation workspace
    workspace = Path('data/annotations/workspace')
    workspace.mkdir(parents=True, exist_ok=True)
    
    images_dir = workspace / 'images_to_annotate'
    images_dir.mkdir(exist_ok=True)
    
    # Copy images
    print(f"\n📋 Copying images to workspace...")
    
    copied = 0
    for idx, ann in selected:
        img_path = Path('data/raw') / ann['img_local_path']
        
        if img_path.exists():
            dest = images_dir / img_path.name
            shutil.copy(img_path, dest)
            copied += 1
    
    print(f"✅ Copied {copied} images")
    
    # Save metadata
    metadata_file = workspace / 'selected_images.json'
    
    metadata = []
    for idx, ann in selected:
        metadata.append({
            'image_id': Path(ann['img_local_path']).stem,
            'img_path': ann['img_local_path'],
            'caption1': ann['caption1'],
            'caption2': ann['caption2'],
            'context_label': ann.get('context_label', 0)
        })
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Saved metadata to {metadata_file}")
    
    # Create annotation template CSV
    create_annotation_template(workspace, metadata)
    
    print("\n" + "=" * 60)
    print("✅ Annotation workspace ready!")
    print("=" * 60)
    print(f"\nLocation: {workspace.absolute()}")
    print(f"   Images: {images_dir.absolute()}")
    print(f"   Template: {workspace / 'annotation_template.csv'}")
    print(f"\nNext: Start annotating images with Google reverse image search!")

def create_annotation_template(workspace, metadata):
    """Create CSV template for manual annotation"""
    import csv
    
    template_file = workspace / 'annotation_template.csv'
    
    with open(template_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'image_id',
            'reference_caption',
            'url_1', 'caption_1', 'date_1', 'domain_1',
            'url_2', 'caption_2', 'date_2', 'domain_2',
            'url_3', 'caption_3', 'date_3', 'domain_3',
            'url_4', 'caption_4', 'date_4', 'domain_4',
            'url_5', 'caption_5', 'date_5', 'domain_5',
            'notes'
        ])
        
        # Add rows
        for item in metadata:
            writer.writerow([
                item['image_id'],
                item['caption1'],
                '', '', '', '',
                '', '', '', '',
                '', '', '', '',
                '', '', '', '',
                '', '', '', '',
                ''
            ])
    
    print(f"✅ Created annotation template CSV")

if __name__ == "__main__":
    select_500_images()