import json
import numpy as np
import faiss
import pickle
import torch
from sentence_transformers import SentenceTransformer
import os

# --- CONFIGURATION ---
DATA_FILE = "products.json"
INDEX_FILE = "shl_vector_store.faiss"
METADATA_FILE = "shl_metadata.pkl" 
# Switching to an even lighter version if needed, but keeping your original for now
MODEL_NAME = "all-MiniLM-L6-v2" 

def build_vector_db():
    print("🚀 Starting Optimized Vector Database Build...")
    
    # 1. Load Data
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found.")
        return
        
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    print(f"📉 Loaded {len(products)} items.")

    # 2. Prepare Text
    corpus = []
    for item in products:
        t_type_str = ", ".join(item.get('test_type', []))
        text = f"Test Type: {t_type_str}. Name: {item['name']}. Description: {item['description']}"
        corpus.append(text)
    
    # 3. Initialize Model with Memory Optimizations
    print(f"🧠 Loading AI Model ({MODEL_NAME}) on CPU...")
    
    # Force the model to use the CPU and load with lower precision if possible
    model = SentenceTransformer(MODEL_NAME, device='cpu')
    
    # 4. Generate Embeddings (Memory Efficient)
    print("⚡ Generating Embeddings...")
    
    # no_grad() prevents the model from storing extra data for training
    with torch.no_grad():
        model.eval() # Set to evaluation mode
        embeddings = model.encode(
            corpus, 
            show_progress_bar=True, 
            batch_size=16, # Smaller batch size uses less peak RAM
            convert_to_numpy=True
        )
    
    # Convert to float32 for FAISS compatibility
    embeddings = np.array(embeddings).astype("float32")
    
    # 5. Build FAISS Index
    dimension = embeddings.shape[1]
    print(f"🏗️  Building FAISS Index (Dimension: {dimension})...")
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    print(f"✅ Added {index.ntotal} vectors to index.")

    # 6. Save Artifacts
    faiss.write_index(index, INDEX_FILE)
    with open(METADATA_FILE, "wb") as f:
        pickle.dump(products, f)
        
    print("\n🎉 Success! AI Engine Built with optimized memory.")

if __name__ == "__main__":
    build_vector_db()