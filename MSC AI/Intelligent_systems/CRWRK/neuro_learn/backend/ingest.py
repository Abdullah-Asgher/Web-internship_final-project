import os
import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
import shutil
import re

# Configuration
DATA_PATH = "../knowledge_base"
DB_PATH = "./chroma_db"

def extract_metadata(file_path):
    """Extract week and type from filename and parent directory"""
    filename = os.path.basename(file_path)
    dirname = os.path.basename(os.path.dirname(file_path))
    metadata = {"source": filename}
    
    # Combine filename and dirname for search
    search_text = f"{dirname} {filename}"
    
    # Extract Week
    week_match = re.search(r"(?:Week|W)[-_]?0?(\d+)", search_text, re.IGNORECASE)
    if week_match:
        metadata["week"] = int(week_match.group(1))
    else:
        metadata["week"] = 0 # Default to 0 if not found
        
    # Extract Type
    if re.search(r"Lecture", search_text, re.IGNORECASE):
        metadata["type"] = "lecture"
    elif re.search(r"Lab|Tutorial", search_text, re.IGNORECASE):
        metadata["type"] = "lab"
    elif re.search(r"Assignment", search_text, re.IGNORECASE):
        metadata["type"] = "assignment"
    else:
        metadata["type"] = "general"
        
    return metadata

def ingest_docs():
    # Clear existing DB to avoid duplicates
    if os.path.exists(DB_PATH):
        print(f"Clearing existing database at {DB_PATH}...")
        shutil.rmtree(DB_PATH)

    print(f"Scanning for documents in {DATA_PATH}...")
    
    documents = []
    
    # Recursive search for files
    # We look for PDF, TXT, MD, and Python files
    patterns = ["**/*.pdf", "**/*.txt", "**/*.md", "**/*.py"]
    
    for pattern in patterns:
        files = glob.glob(os.path.join(DATA_PATH, pattern), recursive=True)
        print(f"Found {len(files)} files matching {pattern}")
        
        for file_path in files:
            try:
                if file_path.endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                elif file_path.endswith(".md"):
                    loader = UnstructuredMarkdownLoader(file_path)
                else:
                    loader = TextLoader(file_path, encoding="utf-8")
                
                loaded_docs = loader.load()
                
                # Add metadata
                file_metadata = extract_metadata(file_path)
                for doc in loaded_docs:
                    doc.metadata.update(file_metadata)
                    
                documents.extend(loaded_docs)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")

    print(f"Total documents loaded: {len(documents)}")
    
    if not documents:
        print("No documents found! Please check the 'knowledge_base' folder.")
        return

    # Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    # Create Vector Store with Local Embeddings (No API needed!)
    print("Creating Vector Store with local embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Initialize empty vector store
    vector_db = Chroma(embedding_function=embeddings, persist_directory=DB_PATH)
    
    # Batch processing
    batch_size = 20  # Small batch size for free tier
    import time
    
    total_batches = len(chunks) // batch_size + 1
    print(f"Processing {len(chunks)} chunks in {total_batches} batches...")
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        if not batch:
            continue
            
        print(f"Processing batch {i//batch_size + 1}/{total_batches}...")
        try:
            vector_db.add_documents(batch)
            # time.sleep(0.1) # Local embeddings are fast, small sleep just in case
        except Exception as e:
            print(f"Error adding batch {i}: {e}")

    print("Ingestion Complete! Vector DB saved to", DB_PATH)

if __name__ == "__main__":
    ingest_docs()
