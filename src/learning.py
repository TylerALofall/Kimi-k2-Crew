import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

class AdaptiveMemory:
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.short_term = []
        self.long_term = {}
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
    def add_short_term(self, interaction: dict):
        """Add to short-term memory (last 10)"""
        self.short_term.append(interaction)
        if len(self.short_term) > 10:
            self.short_term.pop(0)
    
    def add_long_term(self, concept: str, embedding: np.ndarray, metadata: dict):
        """Add to long-term memory with embedding"""
        concept_hash = hash(concept)
        self.long_term[concept_hash] = {
            'concept': concept,
            'embedding': embedding,
            'metadata': metadata,
            'access_count': 0
        }
    
    def retrieve_relevant(self, query: str, k: int = 5) -> list[dict]:
        """Retrieve most relevant memories"""
        # Vectorize query
        query_vec = self.vectorizer.fit_transform([query]).toarray()
        
        results = []
        for key, memory in self.long_term.items():
            sim = cosine_similarity(query_vec, memory['embedding'].reshape(1, -1))[0][0]
            results.append((sim, memory))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:k]]
    
    def reinforce(self, concept_hash: int):
        """Reinforce memory (increase access count)"""
        if concept_hash in self.long_term:
            self.long_term[concept_hash]['access_count'] += 1
    
    def save(self, path: str = "memory.pkl"):
        """Save memory to disk"""
        with open(path, 'wb') as f:
            pickle.dump({
                'short_term': self.short_term,
                'long_term': self.long_term
            }, f)
    
    def load(self, path: str = "memory.pkl"):
        """Load memory from disk"""
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.short_term = data['short_term']
                self.long_term = data['long_term']
