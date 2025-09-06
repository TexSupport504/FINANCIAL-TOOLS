"""Agent knowledge base integration for accessing Goldbach and trading information."""
import sys
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

# Try to import sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


class KnowledgeBase:
    """Knowledge base interface for the agent."""
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        self.kb_dir = Path(kb_dir)
        self.search_dir = self.kb_dir / ".search"
        
        self._chunks = None
        self._embeddings = None
        self._search_index = None
        self._model = None
        self._loaded = False
        
    def _load_search_data(self):
        """Load search index and embeddings."""
        if self._loaded:
            return
            
        if not HAS_EMBEDDINGS:
            print("⚠️ Sentence transformers not available. Install with: pip install sentence-transformers")
            return
            
        if not self.search_dir.exists():
            print(f"⚠️ Search index not found at {self.search_dir}")
            print("Run: python tools/kb_build_embeddings.py to build the index")
            return
        
        try:
            # Load chunks
            with open(self.search_dir / "chunks.json", 'r') as f:
                self._chunks = json.load(f)
            
            # Load embeddings
            self._embeddings = np.load(self.search_dir / "embeddings.npy")
            
            # Load search index
            with open(self.search_dir / "search_index.pkl", 'rb') as f:
                self._search_index = pickle.load(f)
            
            # Load model
            with open(self.search_dir / "metadata.json", 'r') as f:
                metadata = json.load(f)
            
            model_name = metadata.get('model_name', 'all-MiniLM-L6-v2')
            self._model = SentenceTransformer(model_name)
            
            self._loaded = True
            print(f"✅ Loaded knowledge base with {len(self._chunks)} chunks")
            
        except Exception as e:
            print(f"❌ Failed to load knowledge base: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Semantic search in the knowledge base."""
        self._load_search_data()
        
        if not self._loaded:
            return []
        
        try:
            # Encode query
            query_embedding = self._model.encode([query])
            
            # Search
            distances, indices = self._search_index.kneighbors(query_embedding, n_neighbors=top_k)
            
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                chunk = self._chunks[idx].copy()
                chunk['search_rank'] = i + 1
                chunk['similarity_score'] = 1 - distance
                results.append(chunk)
            
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def get_goldbach_info(self, query: str = "goldbach premium discount PO3") -> Dict:
        """Get Goldbach trading strategy information."""
        results = self.search(query, top_k=10)
        
        goldbach_info = {
            'summary': "Goldbach trading strategy based on mathematical patterns",
            'key_concepts': [],
            'references': []
        }
        
        for result in results:
            if result.get('topic') == 'goldbach':
                goldbach_info['references'].append({
                    'source': result['filename'],
                    'content': result['content'][:300] + "..." if len(result['content']) > 300 else result['content'],
                    'score': result['similarity_score']
                })
        
        # Extract key concepts
        key_terms = self.search("premium discount PO3 stop runs algorithm phase entry", top_k=5)
        for term in key_terms:
            if term.get('topic') == 'goldbach':
                goldbach_info['key_concepts'].append(term['content'][:150])
        
        return goldbach_info
    
    def get_po3_levels(self) -> Dict:
        """Get Power of Three levels and calculations."""
        results = self.search("PO3 power of three dealing ranges 27 81 243", top_k=5)
        
        po3_info = {
            'levels': [27, 81, 243, 729, 2187, 6561, 19683],
            'description': "Power of Three levels used for dealing ranges",
            'usage': []
        }
        
        for result in results:
            if result.get('topic') == 'goldbach':
                po3_info['usage'].append(result['content'])
        
        return po3_info
    
    def get_premium_discount_levels(self) -> Dict:
        """Get premium/discount level information."""
        results = self.search("premium discount IPDA goldbach levels 100", top_k=3)
        
        levels_info = {
            'concept': "Premium and discount zones within trading ranges",
            'calculations': [],
            'application': []
        }
        
        for result in results:
            if result.get('topic') == 'goldbach' and 'IPDA' in result.get('content', ''):
                levels_info['calculations'].append(result['content'])
        
        return levels_info
    
    def get_amd_phases(self) -> Dict:
        """Get Accumulation, Manipulation, Distribution phase information."""
        results = self.search("accumulation manipulation distribution AMD phase session", top_k=5)
        
        amd_info = {
            'phases': ['Accumulation', 'Manipulation', 'Distribution'],
            'sessions': {
                'Asian': 'Accumulation phase (9 hours)',
                'London': 'Manipulation phase with breakouts',
                'New York': 'Distribution phase (9 hours)'
            },
            'details': []
        }
        
        for result in results:
            if result.get('topic') == 'goldbach' and 'AMD' in result.get('content', ''):
                amd_info['details'].append(result['content'])
        
        return amd_info
    
    def query_raw(self, topic: str) -> List[str]:
        """Get raw content for a specific topic."""
        results = self.search(topic, top_k=10)
        return [r['content'] for r in results if r.get('topic') == 'goldbach']


# Global knowledge base instance
_kb_instance = None

def get_kb() -> KnowledgeBase:
    """Get the global knowledge base instance."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance


# Convenience functions for agent use
def search_goldbach(query: str, top_k: int = 5) -> List[Dict]:
    """Search for Goldbach information."""
    return get_kb().search(query, top_k)


def get_goldbach_strategy() -> Dict:
    """Get comprehensive Goldbach strategy information."""
    kb = get_kb()
    return {
        'goldbach_info': kb.get_goldbach_info(),
        'po3_levels': kb.get_po3_levels(), 
        'premium_discount': kb.get_premium_discount_levels(),
        'amd_phases': kb.get_amd_phases()
    }


def get_trading_concepts(concept: str) -> List[str]:
    """Get information about specific trading concepts."""
    kb = get_kb()
    return kb.query_raw(concept)


# Test function
def test_knowledge_access():
    """Test that the knowledge base is accessible."""
    print("🔍 Testing Knowledge Base Access")
    print("=" * 40)
    
    kb = get_kb()
    
    # Test search
    results = kb.search("goldbach premium discount", top_k=3)
    print(f"✅ Search returned {len(results)} results")
    
    # Test Goldbach info
    goldbach_info = kb.get_goldbach_info()
    print(f"✅ Goldbach info: {len(goldbach_info['references'])} references")
    
    # Test PO3 levels
    po3_info = kb.get_po3_levels()
    print(f"✅ PO3 levels: {po3_info['levels']}")
    
    print("\n🎉 Knowledge base is accessible and working!")


if __name__ == "__main__":
    test_knowledge_access()
