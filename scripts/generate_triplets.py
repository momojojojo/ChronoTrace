"""
Generate triplet training data for LoRA
Creates (anchor, positive, negative) caption pairs
"""

import json
import random
from pathlib import Path
from tqdm import tqdm
import sys
sys.path.append('.')

from data.cosmos_loader import load_all_captions

def paraphrase_simple(caption):
    """
    Simple paraphrasing using word substitutions
    This is a placeholder - you can improve with T5 or back-translation
    """
    # Simple synonym replacements
    replacements = {
        'protesters': 'demonstrators',
        'gather': 'assemble',
        'peaceful': 'calm',
        'violent': 'aggressive',
        'battle': 'fight',
        'fire': 'blaze',
        'officials': 'authorities',
        'announce': 'declare',
        'said': 'stated',
        'new': 'recent',
    }
    
    words = caption.split()
    paraphrased = []
    
    for word in words:
        lower_word = word.lower().strip('.,!?')
        if lower_word in replacements:
            paraphrased.append(word.replace(lower_word, replacements[lower_word]))
        else:
            paraphrased.append(word)
    
    return ' '.join(paraphrased)

def create_triplet(anchor_caption, all_captions):
    """
    Create one triplet: (anchor, positive, negative)
    
    anchor: Original caption
    positive: Paraphrase of anchor (similar meaning)
    negative: Random different caption (different meaning)
    """
    # Positive: Paraphrase the anchor
    positive = paraphrase_simple(anchor_caption)
    
    # Negative: Random caption that's not the anchor
    negative = random.choice(all_captions)
    while negative == anchor_caption and len(all_captions) > 1:
        negative = random.choice(all_captions)
    
    return (anchor_caption, positive, negative)

def generate_triplets(n_triplets=50000, output_file='data/processed/training_triplets.json'):
    """
    Generate training triplets from COSMOS captions
    
    Args:
        n_triplets: Number of triplets to generate
        output_file: Where to save the triplets
    """
    print("=" * 60)
    print("Triplet Generation for LoRA Training")
    print("=" * 60)
    
    # Load all captions
    print("\n📥 Loading captions...")
    train_captions = load_all_captions(split='train')
    val_captions = load_all_captions(split='val')
    test_captions = load_all_captions(split='test')
    
    # Combine all captions
    all_captions = train_captions + val_captions + test_captions
    
    print(f"✅ Loaded {len(all_captions):,} total captions")
    print(f"   Training: {len(train_captions):,}")
    print(f"   Validation: {len(val_captions):,}")
    print(f"   Test: {len(test_captions):,}")
    
    # Filter out very short captions (< 5 words)
    all_captions = [c for c in all_captions if len(c.split()) >= 5]
    print(f"   After filtering: {len(all_captions):,} captions")
    
    # Generate triplets
    print(f"\n🔄 Generating {n_triplets:,} triplets...")
    triplets = []
    
    random.seed(42)  # Reproducible
    
    for _ in tqdm(range(n_triplets)):
        # Randomly select an anchor caption
        anchor = random.choice(all_captions)
        
        # Create triplet
        triplet = create_triplet(anchor, all_captions)
        triplets.append(triplet)
    
    # Save triplets
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving triplets to {output_path}...")
    
    # Save as JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for anchor, positive, negative in triplets:
            triplet_dict = {
                'anchor': anchor,
                'positive': positive,
                'negative': negative
            }
            f.write(json.dumps(triplet_dict) + '\n')
    
    print(f"✅ Saved {len(triplets):,} triplets")
    
    # Show examples
    print(f"\n📋 Sample Triplets:")
    print("=" * 60)
    
    for i in range(3):
        anchor, positive, negative = triplets[i]
        print(f"\nTriplet {i+1}:")
        print(f"  Anchor:   {anchor[:80]}...")
        print(f"  Positive: {positive[:80]}...")
        print(f"  Negative: {negative[:80]}...")
    
    print("\n" + "=" * 60)
    print("✅ Triplet generation complete!")
    print("=" * 60)
    print(f"\nNext step: Train LoRA adapter")
    print(f"   python scripts/train_lora.py")
    
    return triplets

if __name__ == "__main__":
    triplets = generate_triplets(n_triplets=50000)