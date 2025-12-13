from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

# Get all documents
collection = db._collection
result = collection.get(limit=10, include=['metadatas'])

print("\n" + "="*50)
print("SAMPLE METADATA FROM CHROMADB:")
print("="*50)

for i, metadata in enumerate(result['metadatas'][:10], 1):
    print(f"\nDocument {i}:")
    print(f"  Source: {metadata.get('source', 'N/A')}")
    print(f"  Week: {metadata.get('week', 'NOT SET')}")
    print(f"  Page: {metadata.get('page', 'N/A')}")
    print(f"  Type: {metadata.get('type', 'N/A')}")
    print(f"  All keys: {list(metadata.keys())}")

print("\n" + "="*50)
print("TESTING WEEK FILTER:")
print("="*50)

# Test filtering by week  
try:
    docs_week_6 = db.similarity_search("summary", k=3, filter={"week": 6})
    print(f"\nDocuments with week=6: {len(docs_week_6)}")
    if docs_week_6:
        for doc in docs_week_6:
            print(f"  - {doc.metadata.get('source', 'Unknown')}")
except Exception as e:
    print(f"Error filtering by week=6: {e}")

try:
    docs_week_5 = db.similarity_search("summary", k=3, filter={"week": 5})
    print(f"\nDocuments with week=5: {len(docs_week_5)}")
    if docs_week_5:
        for doc in docs_week_5:
            print(f"  - {doc.metadata.get('source', 'Unknown')}")
except Exception as e:
    print(f"Error filtering by week=5: {e}")

print("\n✅ Check complete!")
