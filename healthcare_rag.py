import os
import json
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np

# LangChain imports
try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain not available, using fallback RAG system")

class HealthcareRAG:
    def __init__(self, persist_directory: str = "./healthcare_knowledge_db"):
        self.persist_directory = persist_directory
        self.embeddings = None
        self.vector_store = None
        self.documents = []
        self.knowledge_base = {}
        
        # Initialize the system
        self.initialize_knowledge_base()
    
    def initialize_knowledge_base(self):
        """Initialize healthcare knowledge base."""
        try:
            if LANGCHAIN_AVAILABLE:
                self._initialize_langchain_rag()
            else:
                self._initialize_fallback_rag()
                
            print("✅ Healthcare RAG knowledge base initialized successfully!")
            
        except Exception as e:
            print(f"⚠️ RAG initialization error: {e}")
            self._initialize_fallback_rag()
    
    def _initialize_langchain_rag(self):
        """Initialize LangChain-based RAG system."""
        try:
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # Load existing knowledge base if available
            if os.path.exists(self.persist_directory):
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                print(f"📚 Loaded existing knowledge base from {self.persist_directory}")
            else:
                # Create new knowledge base with default medical knowledge
                self._create_default_knowledge_base()
                
        except Exception as e:
            print(f"⚠️ LangChain RAG initialization failed: {e}")
            self._initialize_fallback_rag()
    
    def _initialize_fallback_rag(self):
        """Initialize fallback RAG system without LangChain."""
        print("🔄 Using fallback RAG system...")
        
        # Load existing knowledge base if available
        knowledge_file = Path(self.persist_directory) / "knowledge_base.json"
        if knowledge_file.exists():
            try:
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                print(f"📚 Loaded fallback knowledge base with {len(self.knowledge_base)} entries")
            except Exception as e:
                print(f"⚠️ Error loading fallback knowledge base: {e}")
                self._create_default_knowledge_base()
        else:
            self._create_default_knowledge_base()
    
    def _create_default_knowledge_base(self):
        """Create default healthcare knowledge base."""
        default_knowledge = {
            "mental_health": [
                "Anxiety disorders are characterized by excessive fear and worry. Treatment includes cognitive behavioral therapy (CBT), medication, and lifestyle changes.",
                "Depression symptoms include persistent sadness, loss of interest, changes in sleep and appetite. Treatment involves psychotherapy, medication, and support groups.",
                "Mental health crisis protocols: Immediate assessment, safety planning, crisis intervention, and referral to emergency services."
            ],
            "physical_health": [
                "Diabetes management requires blood sugar monitoring, healthy diet, regular exercise, and medication adherence.",
                "Hypertension treatment includes lifestyle modifications, medication, and regular blood pressure monitoring.",
                "Preventive healthcare includes regular check-ups, vaccinations, screenings, and healthy lifestyle choices."
            ],
            "treatments": [
                "Cognitive Behavioral Therapy (CBT) is effective for anxiety and depression, focusing on changing negative thought patterns.",
                "Mindfulness-based stress reduction (MBSR) reduces stress and improves mental well-being through meditation practices.",
                "Exercise therapy improves mood, reduces anxiety, and enhances overall mental health through regular physical activity."
            ],
            "wellness": [
                "Mental wellness strategies: stress management, social connections, purpose and meaning, and professional support.",
                "Physical wellness: balanced nutrition, regular exercise, adequate sleep, and preventive healthcare.",
                "Social wellness: building relationships, community involvement, and emotional support networks."
            ]
        }
        
        self.knowledge_base = default_knowledge
        self._save_knowledge_base()
        print("📚 Created default healthcare knowledge base")
    
    def add_documents(self, documents: List[Document], source: str = "unknown"):
        """Add documents to the knowledge base."""
        try:
            if LANGCHAIN_AVAILABLE and self.vector_store:
                # Add to LangChain vector store
                self.vector_store.add_documents(documents)
                print(f"✅ Added {len(documents)} documents to LangChain vector store")
            else:
                # Add to fallback knowledge base
                for doc in documents:
                    content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                    category = self._classify_document_content(content)
                    
                    if category not in self.knowledge_base:
                        self.knowledge_base[category] = []
                    
                    self.knowledge_base[category].append({
                        "content": content,
                        "source": source,
                        "category": category
                    })
                
                print(f"✅ Added {len(documents)} documents to fallback knowledge base")
                self._save_knowledge_base()
                
        except Exception as e:
            print(f"⚠️ Error adding documents: {e}")
    
    def _classify_document_content(self, content: str) -> str:
        """Classify document content into categories."""
        content_lower = content.lower()
        
        # Define category keywords
        categories = {
            "mental_health": ["anxiety", "depression", "mental", "psychology", "therapy", "counseling"],
            "physical_health": ["diabetes", "hypertension", "cardiac", "respiratory", "gastrointestinal"],
            "treatments": ["treatment", "therapy", "medication", "procedure", "surgery"],
            "wellness": ["wellness", "prevention", "lifestyle", "nutrition", "exercise"],
            "emergency": ["emergency", "crisis", "urgent", "acute", "critical"],
            "pediatrics": ["pediatric", "child", "infant", "adolescent", "young"],
            "geriatrics": ["geriatric", "elderly", "aging", "senior", "older"]
        }
        
        # Find the best matching category
        best_category = "general"
        max_score = 0
        
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > max_score:
                max_score = score
                best_category = category
        
        return best_category
    
    def retrieve_relevant_context(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        """Retrieve relevant healthcare context for a query."""
        try:
            if LANGCHAIN_AVAILABLE and self.vector_store:
                # Use LangChain vector store
                results = self.vector_store.similarity_search(query, k=k)
                context = []
                for doc in results:
                    context.append({
                        "content": doc.page_content,
                        "source": doc.metadata.get("source", "unknown"),
                        "category": doc.metadata.get("category", "general")
                    })
                return context
            else:
                # Use fallback similarity search
                return self._fallback_similarity_search(query, k)
                
        except Exception as e:
            print(f"⚠️ RAG retrieval error: {e}")
            return self._fallback_similarity_search(query, k)
    
    def _fallback_similarity_search(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        """Fallback similarity search using keyword matching."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        all_entries = []
        for category, entries in self.knowledge_base.items():
            for entry in entries:
                content = entry.get("content", "")
                content_lower = content.lower()
                content_words = set(content_lower.split())
                
                # Calculate simple similarity score
                common_words = query_words.intersection(content_words)
                similarity_score = len(common_words) / max(len(query_words), 1)
                
                all_entries.append({
                    "content": content,
                    "source": entry.get("source", "unknown"),
                    "category": category,
                    "similarity_score": similarity_score
                })
        
        # Sort by similarity score and return top k
        all_entries.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_entries = all_entries[:k]
        
        # Remove similarity score from final output
        for entry in top_entries:
            entry.pop("similarity_score", None)
        
        return top_entries
    
    def enhance_prompt_with_rag(self, user_query: str, conversation_context: str = None) -> Tuple[str, List[Dict[str, str]]]:
        """Enhance prompt with relevant healthcare knowledge."""
        # Retrieve relevant context
        relevant_context = self.retrieve_relevant_context(user_query)
        
        # Build enhanced prompt
        enhanced_prompt = f"""
        You are a professional healthcare AI assistant with access to comprehensive medical knowledge.

        RELEVANT HEALTHCARE KNOWLEDGE:
        {chr(10).join([f"• {ctx['content']} (Source: {ctx['source']})" for ctx in relevant_context])}

        CONVERSATION CONTEXT:
        {conversation_context if conversation_context else "No previous context"}

        USER QUERY: {user_query}

        INSTRUCTIONS:
        1. Use the provided healthcare knowledge to inform your response
        2. Provide evidence-based information from the knowledge base
        3. Always include safety disclaimers
        4. Recommend consulting healthcare professionals when appropriate
        5. Cite relevant sources when possible
        6. Be comprehensive, accurate, and supportive

        RESPONSE:
        """
        
        return enhanced_prompt, relevant_context
    
    def save_knowledge_base(self):
        """Save the knowledge base to disk."""
        try:
            if LANGCHAIN_AVAILABLE and self.vector_store:
                self.vector_store.persist()
                print("✅ LangChain knowledge base saved")
            else:
                # Save fallback knowledge base
                os.makedirs(self.persist_directory, exist_ok=True)
                knowledge_file = Path(self.persist_directory) / "knowledge_base.json"
                
                with open(knowledge_file, 'w', encoding='utf-8') as f:
                    json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
                
                print("✅ Fallback knowledge base saved")
                
        except Exception as e:
            print(f"⚠️ Error saving knowledge base: {e}")
    
    def get_knowledge_base_size(self) -> int:
        """Get the size of the knowledge base."""
        if LANGCHAIN_AVAILABLE and self.vector_store:
            try:
                return len(self.vector_store.get()["documents"])
            except:
                return 0
        else:
            total_entries = sum(len(entries) for entries in self.knowledge_base.values())
            return total_entries
    
    def get_knowledge_base_info(self) -> Dict[str, any]:
        """Get information about the knowledge base."""
        info = {
            "total_entries": self.get_knowledge_base_size(),
            "system_type": "langchain" if LANGCHAIN_AVAILABLE and self.vector_store else "fallback",
            "categories": list(self.knowledge_base.keys()) if not LANGCHAIN_AVAILABLE else [],
            "persist_directory": self.persist_directory
        }
        
        if not LANGCHAIN_AVAILABLE:
            info["category_counts"] = {
                category: len(entries) for category, entries in self.knowledge_base.items()
            }
        
        return info

