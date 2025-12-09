"""
COSMOS dataset loader - Complete version with caption-only mode
"""

import json
from pathlib import Path
from PIL import Image
from torch.utils.data import Dataset
from typing import List, Dict, Optional

class COSMOSDataset(Dataset):
    """COSMOS dataset for PyTorch - JSONL format with optional image loading"""
    
    def __init__(
        self, 
        split='test',
        data_dir='data/raw',
        transform=None,
        return_ooc_labels=True,
        load_images=True
    ):
        """
        Args:
            split: 'train', 'val', or 'test'
            data_dir: Root data directory
            transform: Optional image transforms
            return_ooc_labels: Whether to return OOC labels (only for test)
            load_images: Whether to load actual images (False for caption-only mode)
        """
        self.split = split
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.return_ooc_labels = return_ooc_labels
        self.load_images = load_images
        
        # Load annotations (JSONL format)
        ann_path = self.data_dir / f'{split}_data.json'
        
        if not ann_path.exists():
            raise FileNotFoundError(f"Annotation file not found: {ann_path}")
        
        self.annotations = self._load_jsonl(ann_path)
        
        mode = "with images" if load_images else "caption-only"
        print(f"✅ Loaded COSMOS {split} split: {len(self.annotations):,} samples ({mode})")
    
    def _load_jsonl(self, filepath):
        """Load JSONL format (one JSON object per line)"""
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Warning: Skipping line {line_num}: {e}")
        return data
    
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        """Get a single sample"""
        ann = self.annotations[idx]
        
        # Get image path from annotation
        img_rel_path = ann['img_local_path']  # e.g., "test/0.jpg"
        image_id = Path(img_rel_path).stem
        
        # Load image only if requested
        image = None
        if self.load_images:
            img_path = self.data_dir / img_rel_path
            
            if not img_path.exists():
                raise FileNotFoundError(f"Image not found: {img_path}")
            
            image = Image.open(img_path).convert('RGB')
            
            if self.transform:
                image = self.transform(image)
        
        # Prepare output - structure depends on split
        if self.split == 'test':
            # Test split has caption1, caption2, context_label
            sample = {
                'image': image,
                'image_id': image_id,
                'img_path': img_rel_path,
                'caption1': ann['caption1'],
                'caption2': ann['caption2'],
            }
            
            # Add OOC label if requested
            if self.return_ooc_labels:
                sample['context_label'] = ann['context_label']
                sample['article_url'] = ann.get('article_url', '')
            
        else:
            # Train/Val splits have 'articles' array
            sample = {
                'image': image,
                'image_id': image_id,
                'img_path': img_rel_path,
                'articles': ann.get('articles', []),
                'captions': self._extract_captions_from_articles(ann.get('articles', []))
            }
        
        return sample
    
    def _extract_captions_from_articles(self, articles):
        """Extract captions from articles array"""
        captions = []
        
        if not articles:
            return captions
        
        if isinstance(articles, list):
            for article in articles:
                if isinstance(article, dict):
                    # Try multiple possible caption fields
                    caption = (article.get('caption') or 
                              article.get('title') or 
                              article.get('text') or 
                              article.get('description') or
                              '')
                    if caption and isinstance(caption, str):
                        captions.append(caption)
                elif isinstance(article, str):
                    captions.append(article)
        
        return captions
    
    def get_all_captions(self) -> List[str]:
        """Get all captions for LoRA training (no image loading needed)"""
        captions = []
        
        for ann in self.annotations:
            if self.split == 'test':
                # Test split has caption1 and caption2
                captions.append(ann['caption1'])
                captions.append(ann['caption2'])
            else:
                # Train/Val splits have articles
                articles = ann.get('articles', [])
                captions.extend(self._extract_captions_from_articles(articles))
        
        return captions
    
    def filter_by_context_label(self, label=1):
        """
        Filter test samples by context label
        
        Args:
            label: 0 (not OOC) or 1 (OOC)
        
        Returns:
            List of indices matching the label
        """
        if self.split != 'test':
            raise ValueError("Context labels only available in test split")
        
        indices = []
        for idx, ann in enumerate(self.annotations):
            if ann.get('context_label') == label:
                indices.append(idx)
        
        return indices
    
    def get_ooc_statistics(self):
        """Get statistics about OOC labels in test set"""
        if self.split != 'test':
            raise ValueError("Context labels only available in test split")
        
        total = len(self.annotations)
        ooc_count = sum(1 for ann in self.annotations if ann.get('context_label') == 1)
        not_ooc_count = total - ooc_count
        
        return {
            'total': total,
            'ooc': ooc_count,
            'not_ooc': not_ooc_count,
            'ooc_percentage': (ooc_count / total * 100) if total > 0 else 0
        }


# Utility function for caption-only loading
def load_all_captions(split='train', data_dir='data/raw'):
    """
    Quick function to load all captions without creating dataset
    Useful for LoRA training preparation
    
    Args:
        split: 'train', 'val', or 'test'
        data_dir: Root data directory
    
    Returns:
        List of caption strings
    """
    dataset = COSMOSDataset(
        split=split, 
        data_dir=data_dir,
        load_images=False,
        return_ooc_labels=False
    )
    return dataset.get_all_captions()


# Test the loader
if __name__ == "__main__":
    print("=" * 60)
    print("COSMOS Dataset Loader Test")
    print("=" * 60)
    
    # Test 1: Load test set with images
    print("\n📊 Test 1: Test Set (with images)")
    print("-" * 60)
    
    test_dataset = COSMOSDataset(split='test', load_images=True)
    
    # Get statistics
    stats = test_dataset.get_ooc_statistics()
    print(f"\nStatistics:")
    print(f"   Total samples: {stats['total']:,}")
    print(f"   OOC samples: {stats['ooc']:,} ({stats['ooc_percentage']:.1f}%)")
    print(f"   Not OOC samples: {stats['not_ooc']:,}")
    
    # Get first sample
    sample = test_dataset[0]
    print(f"\nFirst Sample:")
    print(f"   Image ID: {sample['image_id']}")
    print(f"   Image shape: {sample['image'].size if sample['image'] else 'None'}")
    print(f"   Context: {sample['context_label']} {'(OOC)' if sample['context_label'] == 1 else '(Not OOC)'}")
    print(f"   Caption 1: {sample['caption1'][:80]}...")
    print(f"   Caption 2: {sample['caption2'][:80]}...")
    
    # Test 2: Load test captions
    print("\n" + "=" * 60)
    print("📊 Test 2: Test Captions (for LoRA)")
    print("-" * 60)
    
    test_captions = test_dataset.get_all_captions()
    print(f"\nTotal test captions: {len(test_captions):,}")
    print(f"Example: {test_captions[0][:80]}...")
    
    # Test 3: Load training captions (no images)
    print("\n" + "=" * 60)
    print("📊 Test 3: Training Captions (caption-only mode)")
    print("-" * 60)
    
    try:
        # Load training dataset without images
        train_dataset = COSMOSDataset(
            split='train', 
            load_images=False,
            return_ooc_labels=False
        )
        
        # Get sample
        train_sample = train_dataset[0]
        print(f"\nFirst Training Sample:")
        print(f"   Image ID: {train_sample['image_id']}")
        print(f"   Image loaded: {train_sample['image'] is not None}")
        print(f"   Articles: {len(train_sample['articles'])}")
        print(f"   Captions extracted: {len(train_sample['captions'])}")
        
        if train_sample['captions']:
            print(f"   First caption: {train_sample['captions'][0][:80]}...")
        
        # Get all training captions
        print(f"\nExtracting all training captions...")
        train_captions = train_dataset.get_all_captions()
        print(f"✅ Total training captions: {len(train_captions):,}")
        
        if train_captions:
            print(f"   Example: {train_captions[0][:80]}...")
        else:
            print("   ⚠️  No captions extracted - checking structure...")
            
            # Debug: Show first annotation structure
            if train_dataset.annotations:
                first_ann = train_dataset.annotations[0]
                print(f"\n   First annotation keys: {list(first_ann.keys())}")
                
                if 'articles' in first_ann:
                    articles = first_ann['articles']
                    print(f"   Articles type: {type(articles)}")
                    print(f"   Articles length: {len(articles) if isinstance(articles, list) else 'N/A'}")
                    
                    if isinstance(articles, list) and len(articles) > 0:
                        print(f"   First article type: {type(articles[0])}")
                        print(f"   First article: {str(articles[0])[:200]}...")
        
    except Exception as e:
        print(f"❌ Error loading training data: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Quick caption loading function
    print("\n" + "=" * 60)
    print("📊 Test 4: Quick Caption Loading Function")
    print("-" * 60)
    
    try:
        val_captions = load_all_captions(split='val')
        print(f"\n✅ Validation captions: {len(val_captions):,}")
        if val_captions:
            print(f"   Example: {val_captions[0][:80]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Summary")
    print("=" * 60)
    print(f"\nDataset loaded successfully!")
    print(f"   Test samples: {len(test_dataset):,} (with images)")
    print(f"   Test captions: {len(test_captions):,}")
    
    try:
        print(f"   Training captions: {len(train_captions):,}")
        print(f"\n🎉 Ready for LoRA training with {len(train_captions):,} caption pairs!")
    except:
        print(f"   Training captions: Check articles structure")
    
    print("\nNext steps:")
    print("   1. Generate triplets from captions")
    print("   2. Train LoRA adapter")
    print("   3. Select 500 images for temporal annotation")