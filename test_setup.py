"""Test if everything is installed correctly"""

def test_imports():
    """Test all critical imports"""
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        
        import transformers
        print(f"✅ Transformers {transformers.__version__}")
        
        import peft
        print(f"✅ PEFT installed")
        
        import sentence_transformers
        print(f"✅ Sentence-Transformers installed")
        
        import networkx as nx
        print(f"✅ NetworkX {nx.__version__}")
        
        print("\n🎉 All dependencies installed successfully!")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")

if __name__ == "__main__":
    test_imports()