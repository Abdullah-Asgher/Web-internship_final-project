"""
RAG (Retrieval Augmented Generation) Module
Handles knowledge retrieval from the vector database
"""
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
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
        
        # Initialize the LLM (OpenAI GPT)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_key=api_key,
            temperature=0.7
        )
        
        # Create the retrieval chain
        self.retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
        
    
    def _web_search_fallback(self, question: str) -> tuple:
        """
        Fallback to web search when knowledge base doesn't have the answer
        Returns: (answer_text, source_urls_list)
        """
        try:
            from googlesearch import search
            import requests
            from bs4 import BeautifulSoup
            
            # Search for relevant pages
            search_results = list(search(f"Intelligent Systems {question}", num_results=3, lang="en"))
            
            if not search_results:
                return None, []
            
            # Try to get snippet from first result
            context_snippets = []
            for url in search_results[:2]:  # Only use first 2 for context
                try:
                    response = requests.get(url, timeout=3)
                    if response.status_code == 200:
                        # Simple text extraction (first 500 chars)
                        text = response.text[:1000]
                        context_snippets.append(f"From {url}: {text[:200]}...")
                except:
                    continue
            
            # Use LLM to synthesize answer from web results
            web_prompt = f"""Based on these web search results about Intelligent Systems:

{chr(10).join(context_snippets) if context_snippets else 'Search results found but could not retrieve content.'}

Question: {question}

Please provide a helpful answer. Mention that this information is from external sources, not the course materials.

Answer:"""
            
            try:
                response = self.llm.invoke(web_prompt)
                content = self._extract_content(response)
                return content, search_results
            except:
                return None, search_results
                
        except Exception as e:
            print(f"Web search failed: {e}")
            return None, []
    
    def _extract_content(self, response):
        """Extract text content from LLM response"""
        content = response.content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
                else:
                    text_parts.append(str(item))
            content = " ".join(text_parts)
        return content
    
    def query(self, question: str, context: str = "", filters: dict = None) -> dict:
        """
        Query the RAG system with fallback to web search
        Returns: {
            'answer': str,
            'sources': list of source documents or URLs,
            'in_knowledge_base': bool
        }
        """
        try:
            # Step 1: Try to retrieve from knowledge base
            try:
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
            except Exception as e:
                print(f"⚠️ Knowledge base retrieval failed: {e}")
                docs = []
            
            # Step 2: Check if we have good knowledge base results
            has_relevant_docs = len(docs) > 0
            
            if has_relevant_docs:
                # Build context from retrieved docs
                retrieved_context = "\n\n".join([
                    f"Source: {os.path.basename(doc.metadata.get('source', 'Unknown'))}, Page: {doc.metadata.get('page', 'N/A')}\nContent: {doc.page_content}" 
                    for doc in docs
                ])
                
                # Create prompt
                prompt_template = """You are an intelligent tutor for the "Intelligent Systems" course. 

Your knowledge base (course materials) contains:
{context}

Additional context: {additional_context}

Student Question: {question}

Instructions:
1. Provide a clear, educational explanation based on the course materials above.
2. ALWAYS cite your sources at the end (e.g., "**Sources:** Week 6 Lecture Slides (Page 12), Week 3 Agent Adaptability (Page 28)").
3. Be encouraging and supportive.
4. Use examples when helpful.
5. If the materials don't fully answer the question, use your general knowledge to supplement, but clearly distinguish what's from the course vs general knowledge.

Answer:"""
                
                prompt = PromptTemplate(
                    template=prompt_template,
                    input_variables=["context", "additional_context", "question"]
                )
                
                # Generate answer
                max_retries = 2
                retry_delay = 5
                
                for attempt in range(max_retries):
                    try:
                        formatted_prompt = prompt.format(
                            context=retrieved_context,
                            additional_context=context,
                            question=question
                        )
                        
                        response = self.llm.invoke(formatted_prompt)
                        content = self._extract_content(response)
                        
                        return {
                            "answer": content,
                            "sources": docs,
                            "in_knowledge_base": True
                        }
                    except Exception as e:
                        error_msg = str(e)
                        if '429' in error_msg or 'rate' in error_msg.lower() or 'quota' in error_msg.lower():
                            # Rate limit error - retry after delay
                            if attempt < max_retries - 1:
                                import time
                                print(f"⏸️  Rate limited. Waiting {retry_delay}s before retry {attempt + 2}/{max_retries}...")
                                time.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff
                                continue
                            else:
                                # Final retry failed - return friendly message with sources
                                print(f"⚠️ Rate limit persists after {max_retries} attempts")
                                return {
                                    "answer": f"I found relevant information in the course materials, but the system is currently experiencing high demand. Please try again in a few moments.\n\n**Found in**: {', '.join(set([os.path.basename(doc.metadata.get('source', 'Unknown')) for doc in docs[:3]]))}",
                                    "sources": docs,
                                    "in_knowledge_base": True
                                }
                        else:
                            # Non-rate-limit error
                            print(f"⚠️ LLM error: {error_msg[:200]}")
                            # Still return what we found, don't fall back to web if we have docs
                            sources_list = [f"{os.path.basename(doc.metadata.get('source', 'Unknown'))} (Page {doc.metadata.get('page', 'N/A')})" for doc in docs[:5]]
                            return {
                                "answer": f"I found relevant course materials but encountered a technical issue processing them. Here's what I found:\n\n**Sources**: {', '.join(set(sources_list))}\n\nPlease try rephrasing your question or try again in a moment.",
                                "sources": docs,
                                "in_knowledge_base": True
                            }
            
            # Step 3: ONLY use web search if we truly found NO documents
            if not has_relevant_docs:
                print("📡 No course materials found. Falling back to web search...")
                web_answer, web_urls = self._web_search_fallback(question)
                
                if web_answer:
                    # Format web sources for display
                    web_sources = [{"source": url, "page": "Web"} for url in web_urls]
                    formatted_answer = f"{web_answer}\n\n**Note:** This answer is from external web sources, not from the course materials.\n**Web Sources:** {', '.join(web_urls[:3])}"
                    
                    return {
                        "answer": formatted_answer,
                        "sources": web_sources,
                        "in_knowledge_base": False
                    }
                else:
                    # Last resort fallback
                    return {
                        "answer": "I apologize, but I'm having trouble finding information about that right now. Could you try rephrasing your question or asking about a specific week/topic from the Intelligent Systems course?",
                        "sources": [],
                        "in_knowledge_base": False
                    }
                    
        except Exception as e:
            # Catch-all error handler - never show technical errors to students
            print(f"❌ Critical error in query: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "answer": "I apologize, but I encountered a technical issue. Please try asking your question again. If the problem persists, please contact your instructor.",
                "sources": [],
                "in_knowledge_base": False
            }
