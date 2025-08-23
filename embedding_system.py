import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingSystem:
    """
    Advanced embedding system that implements the "Convert Docs to Embeddings" 
    and "Chroma DB Vector Index" parts of the RAG workflow.
    
    This system converts text chunks into numerical embeddings and stores them
    in ChromaDB for efficient retrieval.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model = None
        self.vector_store = None
        self._initialize_embedding_model()
        self._initialize_vector_store()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model for converting text to vectors."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not available")
            self.embedding_model = None
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.embedding_model = None
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store for storing embeddings."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create persistent ChromaDB instance
            self.vector_store = chromadb.PersistentClient(
                path="./healthcare_knowledge_db",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection for medical knowledge
            self.collection = self.vector_store.get_or_create_collection(
                name="medical_knowledge",
                metadata={"description": "Medical knowledge base embeddings"}
            )
            
            logger.info("ChromaDB vector store initialized successfully")
            
        except ImportError:
            logger.error("chromadb not available")
            self.vector_store = None
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            self.vector_store = None
    
    def create_embeddings(self, chunks: List[Dict[str, str]]) -> List[Tuple[str, List[float], Dict]]:
        """
        Convert text chunks to embeddings using the embedding model.
        This implements the "Convert Docs to Embeddings" step from the RAG workflow.
        """
        if not self.embedding_model:
            logger.error("Embedding model not available")
            return []
        
        embeddings = []
        logger.info(f"Creating embeddings for {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            try:
                # Create embedding for the chunk content
                text = chunk['content']
                embedding = self.embedding_model.encode(text).tolist()
                
                # Prepare metadata for storage
                metadata = {
                    'source': chunk['source'],
                    'chunk_id': chunk['id'],
                    'chunk_size': chunk['chunk_size'],
                    'type': 'medical_knowledge'
                }
                
                embeddings.append((chunk['id'], embedding, metadata))
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(chunks)} chunks...")
                    
            except Exception as e:
                logger.error(f"Error creating embedding for chunk {chunk['id']}: {e}")
                continue
        
        logger.info(f"Created {len(embeddings)} embeddings successfully")
        return embeddings
    
    def store_embeddings(self, embeddings: List[Tuple[str, List[float], Dict]]) -> bool:
        """
        Store embeddings in ChromaDB vector index in batches.
        This implements the "Chroma DB Vector Index" storage from the RAG workflow.
        """
        if not self.vector_store or not self.collection:
            logger.error("Vector store not available")
            return False
        
        try:
            # ChromaDB batch size limit (conservative)
            BATCH_SIZE = 5000
            total_stored = 0
            
            # Process embeddings in batches
            for i in range(0, len(embeddings), BATCH_SIZE):
                batch = embeddings[i:i + BATCH_SIZE]
                
                # Prepare batch data for ChromaDB
                ids = [emb[0] for emb in batch]
                vectors = [emb[1] for emb in batch]
                metadatas = [emb[2] for emb in batch]
                
                # Store batch in ChromaDB
                self.collection.add(
                    ids=ids,
                    embeddings=vectors,
                    metadatas=metadatas
                )
                
                total_stored += len(batch)
                logger.info(f"Stored batch {i//BATCH_SIZE + 1}: {len(batch)} embeddings (Total: {total_stored}/{len(embeddings)})")
            
            logger.info(f"Successfully stored all {len(embeddings)} embeddings in batches")
            return True
            
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            return False
    
    def search_similar_chunks(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Perform semantic similarity search to find relevant chunks.
        This implements the "Semantic Similarity Search" from the RAG workflow.
        """
        if not self.embedding_model or not self.vector_store:
            logger.error("Embedding system not fully initialized")
            return []
        
        try:
            # Create embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search for similar chunks
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['metadatas', 'distances']
            )
            
            # Format results
            similar_chunks = []
            if results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    chunk_info = {
                        'id': chunk_id,
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'content': self._get_chunk_content(chunk_id)
                    }
                    similar_chunks.append(chunk_info)
            
            logger.info(f"Found {len(similar_chunks)} similar chunks for query")
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching for similar chunks: {e}")
            return []
    
    def _get_chunk_content(self, chunk_id: str) -> str:
        """Retrieve the actual content of a chunk from storage."""
        try:
            # This would typically retrieve from a document store
            # For now, we'll return a placeholder
            return f"Content for chunk: {chunk_id}"
        except Exception as e:
            logger.error(f"Error retrieving chunk content: {e}")
            return ""
    
    def get_vector_store_info(self) -> Dict:
        """Get information about the vector store."""
        if not self.vector_store:
            return {"status": "not_initialized"}
        
        try:
            collection_info = self.collection.get()
            return {
                "status": "active",
                "total_embeddings": len(collection_info['ids']) if collection_info['ids'] else 0,
                "collection_name": "medical_knowledge",
                "database_path": "./healthcare_knowledge_db"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def process_and_store_chunks(self, chunks: List[Dict[str, str]]) -> bool:
        """
        Complete pipeline: process chunks, create embeddings, and store them.
        This implements the complete left side of the RAG workflow diagram.
        """
        logger.info("Starting complete RAG processing pipeline...")
        
        # Step 1: Create embeddings from chunks
        embeddings = self.create_embeddings(chunks)
        if not embeddings:
            logger.error("Failed to create embeddings")
            return False
        
        # Step 2: Store embeddings in vector database
        success = self.store_embeddings(embeddings)
        if not success:
            logger.error("Failed to store embeddings")
            return False
        
        logger.info("Complete RAG processing pipeline completed successfully!")
        return True
    
    def reset_knowledge_base(self) -> bool:
        """Reset the entire knowledge base (useful for testing)."""
        if not self.vector_store:
            return False
        
        try:
            self.vector_store.reset()
            logger.info("Knowledge base reset successfully")
            return True
        except Exception as e:
            logger.error(f"Error resetting knowledge base: {e}")
            return False
