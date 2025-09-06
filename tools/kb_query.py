"""Query the knowledge base using semantic search."""
import json
import pickle
import argparse
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer


def load_search_data(search_dir: str = "knowledge_base/.search"):
    """Load the search index and metadata."""
    search_path = Path(search_dir)
    
    if not search_path.exists():
        raise FileNotFoundError(f"Search directory not found: {search_dir}")
    
    # Load chunks
    with open(search_path / "chunks.json", 'r') as f:
        chunks = json.load(f)
    
    # Load embeddings
    embeddings = np.load(search_path / "embeddings.npy")
    
    # Load search index
    with open(search_path / "search_index.pkl", 'rb') as f:
        search_index = pickle.load(f)
    
    # Load metadata
    with open(search_path / "metadata.json", 'r') as f:
        metadata = json.load(f)
    
    return chunks, embeddings, search_index, metadata


def semantic_search(query: str, chunks: List[Dict], embeddings: np.ndarray, 
                   search_index, model: SentenceTransformer, top_k: int = 5) -> List[Dict]:
    """Perform semantic search on the knowledge base."""
    
    # Encode the query
    query_embedding = model.encode([query])
    
    # Find nearest neighbors
    distances, indices = search_index.kneighbors(query_embedding, n_neighbors=top_k)
    
    results = []
    for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
        chunk = chunks[idx].copy()
        chunk['search_rank'] = i + 1
        chunk['similarity_score'] = 1 - distance  # Convert distance to similarity
        results.append(chunk)
    
    return results


def print_search_results(results: List[Dict], query: str):
    """Pretty print search results."""
    print(f"\n🔍 SEARCH RESULTS FOR: '{query}'")
    print("=" * 60)
    
    for result in results:
        rank = result['search_rank']
        score = result['similarity_score']
        topic = result['topic']
        filename = result['filename']
        content = result['content']
        
        # Truncate content for display
        preview = content[:200] + "..." if len(content) > 200 else content
        preview = preview.replace('\n', ' ').strip()
        
        print(f"\n📄 RESULT #{rank} (Score: {score:.3f})")
        print(f"   Topic: {topic}")
        print(f"   File: {filename}")
        print(f"   Preview: {preview}")


def interactive_search():
    """Interactive search mode."""
    print("🚀 KNOWLEDGE BASE SEARCH")
    print("=" * 30)
    
    # Load search data
    print("🔄 Loading search index...")
    try:
        chunks, embeddings, search_index, metadata = load_search_data()
        print(f"✅ Loaded {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Failed to load search data: {e}")
        return
    
    # Load model
    model_name = metadata.get('model_name', 'all-MiniLM-L6-v2')
    print(f"🔄 Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    print("\n💡 Type your search queries. Type 'quit' to exit.")
    print("Examples:")
    print("  - premium discount levels")
    print("  - PO3 stop runs")
    print("  - goldbach algorithm")
    print("  - accumulation manipulation distribution")
    
    while True:
        print("\n" + "-" * 40)
        query = input("🔍 Search: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not query:
            continue
        
        try:
            results = semantic_search(query, chunks, embeddings, search_index, model)
            print_search_results(results, query)
        except Exception as e:
            print(f"❌ Search failed: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Search the knowledge base")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive or not args.query:
        interactive_search()
        return
    
    # Single query mode
    try:
        chunks, embeddings, search_index, metadata = load_search_data()
        model = SentenceTransformer(metadata.get('model_name', 'all-MiniLM-L6-v2'))
        results = semantic_search(args.query, chunks, embeddings, search_index, model, args.top_k)
        print_search_results(results, args.query)
    except Exception as e:
        print(f"❌ Search failed: {e}")


if __name__ == "__main__":
    main()
