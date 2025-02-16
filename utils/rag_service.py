import faiss
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer

class RAGService:
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatL2(384)  # 384 is the embedding dimension
        self.stored_texts: List[Dict] = []

    def add_to_knowledge_base(self, text: str, metadata: Dict):
        embedding = self.encoder.encode([text])[0]
        self.index.add(np.array([embedding]).astype('float32'))
        self.stored_texts.append({"text": text, "metadata": metadata})

    def search(self, query: str, k: int = 5):
        query_embedding = self.encoder.encode([query])[0]
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'), k
        )
        
        results = []
        for idx in indices[0]:
            if idx < len(self.stored_texts):
                results.append(self.stored_texts[idx])
        
        return results