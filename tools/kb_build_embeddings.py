"""Build semantic search embeddings for the knowledge base."""
import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors


def load_markdown_files(kb_dir: str = "knowledge_base") -> List[Dict[str, Any]]:
    """Load all markdown files from the knowledge base."""
    documents = []
    kb_path = Path(kb_dir)
    
    if not kb_path.exists():
        print(f"❌ Knowledge base directory not found: {kb_dir}")
        return documents
    
    for md_file in kb_path.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Skip empty files
            if len(content.strip()) < 50:
                continue
                
            # Extract topic from path
            relative_path = md_file.relative_to(kb_path)
            topic = str(relative_path.parent) if relative_path.parent != Path('.') else 'general'
            
            documents.append({
                'file_path': str(md_file),
                'relative_path': str(relative_path),
                'topic': topic,
                'content': content,
                'filename': md_file.name
            })
            
        except Exception as e:
            print(f"⚠️ Error reading {md_file}: {e}")
            continue
    
    print(f"📚 Loaded {len(documents)} documents")
    return documents


def chunk_documents(documents: List[Dict[str, Any]], chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """Split documents into smaller chunks for better search."""
    chunks = []
    
    for doc in documents:
        content = doc['content']
        
        # Simple chunking by characters
        start = 0
        chunk_id = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to end at sentence boundary
            if end < len(content):
                last_period = content.rfind('.', start, end)
                last_newline = content.rfind('\n', start, end)
                boundary = max(last_period, last_newline)
                
                if boundary > start + chunk_size // 2:
                    end = boundary + 1
            
            chunk_content = content[start:end].strip()
            
            if len(chunk_content) > 20:  # Skip very short chunks
                chunks.append({
                    'chunk_id': f"{doc['filename']}_chunk_{chunk_id}",
                    'file_path': doc['file_path'],
                    'relative_path': doc['relative_path'], 
                    'topic': doc['topic'],
                    'filename': doc['filename'],
                    'content': chunk_content,
                    'start_pos': start,
                    'end_pos': end
                })
                chunk_id += 1
            
            start = end - overlap if end < len(content) else len(content)
    
    print(f"📄 Created {len(chunks)} chunks")
    return chunks


def build_embeddings(chunks: List[Dict[str, Any]], model_name: str = "all-MiniLM-L6-v2") -> tuple:
    """Build embeddings for all chunks."""
    print(f"🔄 Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    print("🔄 Generating embeddings...")
    texts = [chunk['content'] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print(f"✅ Generated embeddings: {embeddings.shape}")
    return model, embeddings


def build_search_index(embeddings: np.ndarray, n_neighbors: int = 10) -> NearestNeighbors:
    """Build KNN search index."""
    print("🔄 Building search index...")
    index = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
    index.fit(embeddings)
    print("✅ Search index built")
    return index


def save_search_data(chunks: List[Dict[str, Any]], embeddings: np.ndarray, 
                    index: NearestNeighbors, output_dir: str = "knowledge_base/.search"):
    """Save all search data to disk."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save chunks metadata
    with open(output_path / "chunks.json", 'w') as f:
        json.dump(chunks, f, indent=2)
    
    # Save embeddings
    np.save(output_path / "embeddings.npy", embeddings)
    
    # Save search index
    with open(output_path / "search_index.pkl", 'wb') as f:
        pickle.dump(index, f)
    
    # Save metadata
    metadata = {
        'num_chunks': len(chunks),
        'embedding_dim': embeddings.shape[1],
        'model_name': 'all-MiniLM-L6-v2',
        'created': str(Path().resolve())
    }
    
    with open(output_path / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Saved search data to: {output_path}")


def main():
    """Build the complete knowledge base search system."""
    print("🚀 BUILDING KNOWLEDGE BASE EMBEDDINGS")
    print("=" * 50)
    
    # Load documents
    documents = load_markdown_files()
    if not documents:
        print("❌ No documents found!")
        return
    
    # Create chunks
    chunks = chunk_documents(documents, chunk_size=500, overlap=50)
    if not chunks:
        print("❌ No chunks created!")
        return
    
    # Build embeddings
    model, embeddings = build_embeddings(chunks)
    
    # Build search index
    index = build_search_index(embeddings)
    
    # Save everything
    save_search_data(chunks, embeddings, index)
    
    print("\n✅ Knowledge base embeddings built successfully!")
    print("📋 Summary:")
    print(f"   Documents processed: {len(documents)}")
    print(f"   Chunks created: {len(chunks)}")
    print(f"   Embedding dimensions: {embeddings.shape[1]}")
    print(f"   Search index neighbors: {index.n_neighbors}")
    
    # Show topic distribution
    topics = {}
    for chunk in chunks:
        topic = chunk['topic']
        topics[topic] = topics.get(topic, 0) + 1
    
    print("\n📊 Topic distribution:")
    for topic, count in sorted(topics.items()):
        print(f"   {topic}: {count} chunks")


if __name__ == "__main__":
    main()
