#!/usr/bin/env python3
"""
Inspect ChromaDB contents - useful for screenshots
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def inspect_chromadb():
    print("=" * 80)
    print("📊 ChromaDB Inspection Report")
    print("=" * 80)
    
    # Load embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Load vector store
    vector_db = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    
    # Get collection stats
    collection = vector_db._collection
    count = collection.count()
    
    print(f"\n✅ Total Documents in Database: {count}")
    
    # Sample query to show metadata
    print(f"\n🔍 Sample Query: 'What is reinforcement learning?'")
    print("-" * 80)
    
    results = vector_db.similarity_search(
        "What is reinforcement learning?",
        k=5
    )
    
    print(f"\nTop 5 Retrieved Documents:")
    for i, doc in enumerate(results, 1):
        print(f"\n📄 Document {i}:")
        print(f"   Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"   Week: {doc.metadata.get('week', 'N/A')}")
        print(f"   Type: {doc.metadata.get('type', 'N/A')}")
        print(f"   Page: {doc.metadata.get('page', 'N/A')}")
        print(f"   Content Preview: {doc.page_content[:150]}...")
    
    # Show week distribution
    print(f"\n📊 Week Distribution:")
    print("-" * 80)
    
    # Query for each week
    for week in range(1, 10):
        week_docs = vector_db.similarity_search(
            "summary",
            k=100,
            filter={"week": week}
        )
        if week_docs:
            print(f"   Week {week}: {len(week_docs)} documents")
    
    # Show type distribution
    print(f"\n📊 Content Type Distribution:")
    print("-" * 80)
    
    for content_type in ["lecture", "lab", "assignment", "general"]:
        type_docs = vector_db.similarity_search(
            "summary",
            k=100,
            filter={"type": content_type}
        )
        if type_docs:
            print(f"   {content_type.capitalize()}: {len(type_docs)} documents")
    
    print("\n" + "=" * 80)
    print("✅ Inspection Complete!")
    print("=" * 80)

if __name__ == "__main__":
    inspect_chromadb()
