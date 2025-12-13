"""
RAG (Retrieval Augmented Generation) Module
Handles knowledge retrieval from the vector database
"""
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import os

class RAGSystem:
    def __init__(self, db_path="./chroma_db"):
        """Initialize the RAG system with the vector database"""
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings
        )
        
        # Initialize the LLM (Gemini)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
            
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.7
        )
        
        # Create the retrieval chain
        self.retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
        
    def query(self, question: str, context: str = "", filters: dict = None) -> dict:
        """
        Query the RAG system
        Returns: {
            'answer': str,
            'sources': list of source documents,
            'in_knowledge_base': bool
        }
        """
        # Retrieve relevant documents
        if filters:
            print(f"🔍 ChromaDB Query:")
            print(f"   Question: {question}")
            print(f"   Filters: {filters}")
            print(f"   Top-K: 5")
            docs = self.vector_db.similarity_search(question, k=5, filter=filters)
            print(f"✅ Retrieved {len(docs)} documents")
            for i, doc in enumerate(docs, 1):
                print(f"   Doc {i}: {doc.metadata.get('source', 'Unknown')} (Week {doc.metadata.get('week', 'N/A')}, Page {doc.metadata.get('page', 'N/A')})")
        else:
            docs = self.retriever.invoke(question)
            print(f"✅ Retrieved {len(docs)} documents (no filters)")
        
        # Build context from retrieved docs with metadata
        retrieved_context = "\n\n".join([
            f"Source: {os.path.basename(doc.metadata.get('source', 'Unknown'))}, Page: {doc.metadata.get('page', 'N/A')}\nContent: {doc.page_content}" 
            for doc in docs
        ])
        
        # Create prompt
        prompt_template = """You are an intelligent tutor for the "Intelligent Systems" course. 
        
Your knowledge base contains:
{context}

Additional context: {additional_context}

Student Question: {question}

Instructions:
1. If the answer is in the knowledge base above, provide a clear, educational explanation.
2. ALWAYS cite your sources from the knowledge base (e.g., "Source: Lecture1.pdf, Page 12") at the end of your answer.
3. If the answer is NOT in the knowledge base, say: "This topic is outside our current curriculum, but here's what I know from my general knowledge..."
4. Be encouraging and supportive.
5. Use examples when helpful.

Answer:"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "additional_context", "question"]
        )
        
        # Generate answer
        formatted_prompt = prompt.format(
            context=retrieved_context,
            additional_context=context,
            question=question
        )
        
        response = self.llm.invoke(formatted_prompt)
        
        return {
            "answer": response.content,
            "sources": docs,
            "in_knowledge_base": len(docs) > 0 and docs[0].metadata
        }
