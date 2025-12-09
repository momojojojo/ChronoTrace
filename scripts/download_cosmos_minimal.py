"""
Download only essential COSMOS files for ChronoTrace
Saves ~18GB of space!
"""

import os
import requests
from tqdm import tqdm
import zipfile
from pathlib import Path

class COSMOSMinimalDownloader:
    """Download only what's needed for the project"""
    
    BASE_URL = "http://kaldir.vc.in.tum.de"
    
    # Only download essentials
    ESSENTIAL_FILES = {
        'annotations': 'cosmos_anns.zip',      # 3 MB
        'test_images': 'images_test.zip',      # 300 MB
    }
    
    # Optional - only if you want to visualize training samples
    OPTIONAL_FILES = {
        'train_images': 'images_train.zip',    # 15 GB - SKIP THIS
        'val_images': 'images_val.zip',        # 4 GB - SKIP THIS
    }
    
    def __init__(self, data_dir='data/raw'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def download_file(self, filename, desc):
        """Download a single file with progress bar"""
        url = f"{self.BASE_URL}/{filename}"
        filepath = self.data_dir / filename
        
        # Skip if already downloaded
        if filepath.exists():
            print(f"✓ {filename} already exists, skipping...")
            return filepath
        
        print(f"\nDownloading {desc}...")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, tqdm(
                desc=desc,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)
            
            print(f"✅ Downloaded {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")
            return None
    
    def extract_zip(self, zip_path):
        """Extract zip file"""
        print(f"\nExtracting {zip_path.name}...")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                with tqdm(total=len(file_list), desc="Extracting") as pbar:
                    for file in file_list:
                        zip_ref.extract(file, self.data_dir)
                        pbar.update(1)
            
            print(f"✅ Extracted to {self.data_dir}")
            
            # Delete zip to save space
            zip_path.unlink()
            print(f"🗑️  Deleted {zip_path.name} to save space")
                
        except Exception as e:
            print(f"❌ Error extracting {zip_path}: {e}")
    
    def download_essential(self):
        """Download only essential files"""
        print("=" * 60)
        print("COSMOS Minimal Download (< 500 MB)")
        print("=" * 60)
        print("\n💡 Downloading only what you need for LoRA training:")
        print("   • Test images (300 MB) - for evaluation")
        print("   • Annotations (3 MB) - captions for training")
        print("\n⏩ Skipping training/val images to save ~18 GB!")
        print("   (You only need captions, not images, for LoRA)")
        print("=" * 60)
        
        downloaded_files = []
        
        for key, filename in self.ESSENTIAL_FILES.items():
            desc = key.replace('_', ' ').title()
            filepath = self.download_file(filename, desc)
            
            if filepath:
                downloaded_files.append(filepath)
                self.extract_zip(filepath)
        
        print("\n" + "=" * 60)
        print(f"✅ Downloaded {len(downloaded_files)}/{len(self.ESSENTIAL_FILES)} essential files")
        print(f"💾 Total space used: < 500 MB (saved ~18 GB!)")
        print("=" * 60)
        
        self.print_usage_info()
    
    def print_usage_info(self):
        """Print what you can do with minimal download"""
        print("\n📋 What you can do with this minimal download:")
        print("=" * 60)
        print("✅ Train LoRA adapter (uses captions only)")
        print("✅ Evaluate on test set (1,700 images)")
        print("✅ Generate 50,000 training triplets")
        print("✅ Complete entire capstone project")
        print("\n❌ What you CAN'T do (but don't need):")
        print("   • Visualize all 160K training images")
        print("   • Train from scratch (you're using pre-trained)")
        print("=" * 60)

def main():
    """Main download function"""
    print("\n🚀 Starting minimal COSMOS download...")
    print("This will download < 500 MB instead of 20 GB!\n")
    
    confirm = input("Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Download cancelled.")
        return
    
    downloader = COSMOSMinimalDownloader('data/raw')
    downloader.download_essential()
    
    print("\n✅ Setup complete! Next steps:")
    print("   1. Run: python notebooks/01_cosmos_exploration.ipynb")
    print("   2. Start annotating 500 images for temporal sequences")

if __name__ == "__main__":
    main()