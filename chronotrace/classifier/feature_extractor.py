"""
Feature extraction for generic image classification
"""

import requests
from collections import Counter
import numpy as np
from datetime import datetime

class ImageFeatureExtractor:
    """Extract features for generic vs event-specific classification"""
    
    def __init__(self):
        pass
    
    def extract_features(self, image_data):
        """
        Extract 12 features from image metadata
        
        Args:
            image_data: Dict with keys:
                - urls: List of URLs where image appears
                - captions: List of captions for each URL
                - timestamps: List of timestamps (datetime objects)
                - domains: List of domain names
                
        Returns:
            numpy array of 12 features
        """
        features = {}
        
        # Feature 1-4: Web Distribution
        features['url_count'] = len(image_data['urls'])
        features['domain_diversity'] = self._domain_entropy(image_data['domains'])
        features['temporal_spread'] = self._temporal_spread(image_data['timestamps'])
        features['domain_count'] = len(set(image_data['domains']))
        
        # Feature 5-8: Caption Patterns
        features['caption_diversity'] = self._caption_diversity(image_data['captions'])
        features['avg_caption_length'] = np.mean([len(c.split()) for c in image_data['captions']])
        features['unique_word_ratio'] = self._unique_word_ratio(image_data['captions'])
        features['has_specific_entities'] = self._has_entities(image_data['captions'])
        
        # Feature 9-12: Temporal Patterns
        features['reuse_velocity'] = self._reuse_velocity(image_data['timestamps'])
        features['burst_score'] = self._burst_score(image_data['timestamps'])
        features['is_stock_domain'] = self._is_stock_domain(image_data['domains'])
        features['has_watermark'] = image_data.get('has_watermark', 0)  # If available
        
        # Convert to array
        return np.array(list(features.values()))
    
    def _domain_entropy(self, domains):
        """Calculate entropy of domain distribution"""
        if not domains:
            return 0
        counter = Counter(domains)
        probs = np.array(list(counter.values())) / len(domains)
        return -np.sum(probs * np.log2(probs + 1e-10))
    
    def _temporal_spread(self, timestamps):
        """Days between first and last appearance"""
        if len(timestamps) < 2:
            return 0
        sorted_times = sorted(timestamps)
        return (sorted_times[-1] - sorted_times[0]).days
    
    def _caption_diversity(self, captions):
        """Standard deviation of caption lengths"""
        lengths = [len(c.split()) for c in captions]
        return np.std(lengths)
    
    def _unique_word_ratio(self, captions):
        """Ratio of unique words to total words"""
        all_words = ' '.join(captions).lower().split()
        if not all_words:
            return 0
        return len(set(all_words)) / len(all_words)
    
    def _has_entities(self, captions):
        """Check if captions mention specific entities (simple heuristic)"""
        # Look for capitalized sequences (proper nouns)
        entity_count = 0
        for caption in captions:
            words = caption.split()
            for word in words:
                if word and word[0].isupper() and word not in ['The', 'A', 'An']:
                    entity_count += 1
        return min(entity_count / max(len(captions), 1), 1.0)
    
    def _reuse_velocity(self, timestamps):
        """Average time between appearances"""
        if len(timestamps) < 2:
            return 0
        sorted_times = sorted(timestamps)
        gaps = [(sorted_times[i+1] - sorted_times[i]).days for i in range(len(sorted_times)-1)]
        return np.mean(gaps) if gaps else 0
    
    def _burst_score(self, timestamps):
        """Detect temporal bursts (high reuse in short time)"""
        if len(timestamps) < 3:
            return 0
        sorted_times = sorted(timestamps)
        # Count appearances within 7-day windows
        max_burst = 0
        for i in range(len(sorted_times)):
            window_end = sorted_times[i] + np.timedelta64(7, 'D')
            burst_count = sum(1 for t in sorted_times if sorted_times[i] <= t <= window_end)
            max_burst = max(max_burst, burst_count)
        return max_burst / len(timestamps)
    
    def _is_stock_domain(self, domains):
        """Check if any domain is a stock photo site"""
        stock_domains = [
            'shutterstock', 'gettyimages', 'istockphoto', 'adobestock',
            'unsplash', 'pexels', 'pixabay', 'dreamstime'
        ]
        for domain in domains:
            if any(stock in domain.lower() for stock in stock_domains):
                return 1.0
        return 0.0

# Example usage
if __name__ == "__main__":
    extractor = ImageFeatureExtractor()
    
    # Sample data
    sample_image = {
        'urls': ['url1', 'url2', 'url3', 'url4'],
        'captions': [
            'Business meeting', 
            'Corporate discussion',
            'Office teamwork',
            'Professional collaboration'
        ],
        'timestamps': [
            datetime(2024, 1, 1),
            datetime(2024, 2, 15),
            datetime(2024, 5, 20),
            datetime(2024, 8, 10)
        ],
        'domains': ['businesstoday.com', 'forbes.com', 'linkedin.com', 'indeed.com'],
        'has_watermark': 0
    }
    
    features = extractor.extract_features(sample_image)
    print(f"Extracted features: {features}")
    print(f"Feature shape: {features.shape}")