"""
LoRA training module for caption encoding
"""

import torch
from transformers import AutoModel, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import Dataset, DataLoader
import yaml
from pathlib import Path

class TripletDataset(Dataset):
    """Dataset for triplet learning"""
    
    def __init__(self, triplets, tokenizer, max_length=128):
        """
        Args:
            triplets: List of (anchor, positive, negative) caption tuples
            tokenizer: HuggingFace tokenizer
            max_length: Maximum sequence length
        """
        self.triplets = triplets
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.triplets)
    
    def __getitem__(self, idx):
        anchor, positive, negative = self.triplets[idx]
        
        # Tokenize all three
        anchor_enc = self.tokenizer(
            anchor, 
            padding='max_length', 
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        positive_enc = self.tokenizer(
            positive,
            padding='max_length',
            truncation=True, 
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        negative_enc = self.tokenizer(
            negative,
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'anchor': {k: v.squeeze(0) for k, v in anchor_enc.items()},
            'positive': {k: v.squeeze(0) for k, v in positive_enc.items()},
            'negative': {k: v.squeeze(0) for k, v in negative_enc.items()}
        }

class LoRATrainer:
    """Trainer for LoRA-adapted sentence encoder"""
    
    def __init__(self, config_path='config/config.yaml'):
        """Initialize trainer with config"""
        with open(config_path) as f:
            self.config = yaml.safe_load(f)['lora']
            
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._setup_model()
        
    def _setup_model(self):
        """Load base model and apply LoRA"""
        # Load base model
        model_name = self.config['base_model']
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        base_model = AutoModel.from_pretrained(model_name)
        
        # Configure LoRA
        lora_config = LoraConfig(
            r=self.config['rank'],
            lora_alpha=self.config['alpha'],
            target_modules=self.config['target_modules'],
            lora_dropout=self.config['dropout'],
            bias="none",
            task_type=TaskType.FEATURE_EXTRACTION
        )
        
        # Apply LoRA
        self.model = get_peft_model(base_model, lora_config)
        self.model.to(self.device)
        
        print(f"✅ Model loaded on {self.device}")
        self.model.print_trainable_parameters()
        
    def triplet_loss(self, anchor, positive, negative, margin=1.0):
        """Compute triplet loss"""
        # Mean pooling to get sentence embeddings
        anchor_emb = self.mean_pooling(anchor)
        positive_emb = self.mean_pooling(positive)
        negative_emb = self.mean_pooling(negative)
        
        # Compute distances
        pos_dist = torch.nn.functional.pairwise_distance(anchor_emb, positive_emb)
        neg_dist = torch.nn.functional.pairwise_distance(anchor_emb, negative_emb)
        
        # Triplet loss
        loss = torch.nn.functional.relu(pos_dist - neg_dist + margin)
        return loss.mean()
    
    def mean_pooling(self, model_output):
        """Mean pooling over token embeddings"""
        token_embeddings = model_output.last_hidden_state
        attention_mask = model_output.attention_mask
        
        # Expand mask
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        # Sum and average
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        return sum_embeddings / sum_mask
    
    def train(self, triplets, save_dir='models/lora_checkpoints'):
        """
        Train LoRA adapter
        
        Args:
            triplets: List of (anchor, positive, negative) tuples
            save_dir: Where to save checkpoints
        """
        # Create dataset and dataloader
        dataset = TripletDataset(triplets, self.tokenizer)
        dataloader = DataLoader(
            dataset, 
            batch_size=self.config['batch_size'],
            shuffle=True
        )
        
        # Optimizer
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config['learning_rate']
        )
        
        # Training loop
        self.model.train()
        for epoch in range(self.config['num_epochs']):
            total_loss = 0
            
            for batch_idx, batch in enumerate(dataloader):
                # Move to device
                anchor = {k: v.to(self.device) for k, v in batch['anchor'].items()}
                positive = {k: v.to(self.device) for k, v in batch['positive'].items()}
                negative = {k: v.to(self.device) for k, v in batch['negative'].items()}
                
                # Forward pass
                anchor_out = self.model(**anchor)
                positive_out = self.model(**positive)
                negative_out = self.model(**negative)
                
                # Compute loss
                loss = self.triplet_loss(anchor_out, positive_out, negative_out)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                
                if (batch_idx + 1) % 10 == 0:
                    print(f"Epoch {epoch+1}/{self.config['num_epochs']} "
                          f"Batch {batch_idx+1}/{len(dataloader)} "
                          f"Loss: {loss.item():.4f}")
            
            avg_loss = total_loss / len(dataloader)
            print(f"📊 Epoch {epoch+1} Average Loss: {avg_loss:.4f}")
            
        # Save model
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(save_dir)
        self.tokenizer.save_pretrained(save_dir)
        print(f"✅ Model saved to {save_dir}")

# Example usage
if __name__ == "__main__":
    # Sample triplets (replace with real data)
    triplets = [
        ("Protesters gather peacefully", "Demonstrators assemble calmly", "Rioters cause destruction"),
        ("Fire crews battle blaze", "Firefighters fight fire", "Arsonists start inferno"),
    ]
    
    trainer = LoRATrainer()
    trainer.train(triplets)