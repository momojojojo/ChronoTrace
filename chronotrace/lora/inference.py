"""
LoRA inference module for computing caption similarities
"""

import torch
from transformers import AutoTokenizer, AutoModel
from peft import PeftModel
import numpy as np

class LoRAEncoder:
    """Caption encoder using LoRA-adapted model"""
    
    def __init__(self, model_path='models/lora_checkpoints'):
        """Load trained LoRA model"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load base model
        base_model = AutoModel.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Load LoRA weights
        self.model = PeftModel.from_pretrained(base_model, model_path)
        self.model.to(self.device)
        self.model.eval()
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        print(f"✅ LoRA model loaded from {model_path}")
        
    def encode(self, texts, batch_size=32):
        """
        Encode texts to embeddings
        
        Args:
            texts: List of strings or single string
            batch_size: Batch size for encoding
            
        Returns:
            numpy array of embeddings (n_texts, embedding_dim)
        """
        if isinstance(texts, str):
            texts = [texts]
            
        all_embeddings = []
        
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                
                # Tokenize
                encoded = self.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=128,
                    return_tensors='pt'
                )
                
                # Move to device
                encoded = {k: v.to(self.device) for k, v in encoded.items()}
                
                # Get embeddings
                outputs = self.model(**encoded)
                embeddings = self.mean_pooling(outputs, encoded['attention_mask'])
                
                all_embeddings.append(embeddings.cpu().numpy())
        
        return np.vstack(all_embeddings)
    
    def mean_pooling(self, model_output, attention_mask):
        """Mean pooling"""
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask
    
    def similarity(self, text1, text2):
        """
        Compute cosine similarity between two texts
        
        Returns:
            float between 0 and 1
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        
        # Cosine similarity
        dot_product = np.dot(emb1[0], emb2[0])
        norm_product = np.linalg.norm(emb1[0]) * np.linalg.norm(emb2[0])
        
        return float(dot_product / norm_product)

# Example usage
if __name__ == "__main__":
    encoder = LoRAEncoder()
    
    # Test similarity
    caption1 = "Protesters gather peacefully in downtown"
    caption2 = "Demonstrators assemble calmly in city center"
    caption3 = "Rioters cause destruction in urban area"
    
    print(f"Sim(1,2): {encoder.similarity(caption1, caption2):.3f}")  # Should be high
    print(f"Sim(1,3): {encoder.similarity(caption1, caption3):.3f}")  # Should be low