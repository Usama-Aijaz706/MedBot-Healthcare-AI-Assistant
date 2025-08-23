import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import os
from dotenv import load_dotenv

from pdf_processor import PDFProcessor
from embedding_system import EmbeddingSystem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider:
    """Handles different LLM providers (Groq, Gemini, HuggingFace, Azure OpenAI)."""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.azure_openai_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.hf_token = os.getenv('HF_TOKEN')
        self.endpoint_url = os.getenv('ENDPOINT_URL')
        
        # Debug: Print available API keys
        logger.info(f"Available API keys:")
        logger.info(f"  Groq: {'✅' if self.groq_api_key else '❌'}")
        logger.info(f"  Gemini: {'✅' if self.gemini_api_key else '❌'}")
        logger.info(f"  Azure OpenAI: {'✅' if self.azure_openai_key else '❌'}")
        logger.info(f"  HuggingFace: {'✅' if self.hf_token else '❌'}")
        logger.info(f"  Azure Endpoint: {'✅' if self.endpoint_url else '❌'}")
        
        # Default to Groq if available
        self.default_provider = 'groq' if self.groq_api_key else 'gemini' if self.gemini_api_key else 'huggingface'
        logger.info(f"LLM Provider initialized. Default: {self.default_provider}")
    
    def generate_response(self, prompt: str, provider: str = None) -> str:
        """Generate response using the specified LLM provider."""
        if not provider:
            provider = self.default_provider
            
        try:
            if provider == 'groq' and self.groq_api_key:
                return self._call_groq(prompt)
            elif provider == 'gemini' and self.gemini_api_key:
                return self._call_gemini(prompt)
            elif provider == 'azure' and self.azure_openai_key:
                return self._call_azure_openai(prompt)
            elif provider == 'huggingface' and self.hf_token:
                return self._call_huggingface(prompt)
            else:
                logger.warning(f"Provider {provider} not available, using fallback response")
                return self._fallback_response(prompt)
                
        except Exception as e:
            logger.error(f"Error calling {provider}: {e}")
            return self._fallback_response(prompt)
    
    def _call_groq(self, prompt: str) -> str:
        """Call Groq API with openai/gpt-oss-20b model."""
        try:
            import groq
            
            # Use the correct environment variable name
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            client = groq.Groq(api_key=api_key)
            
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                model="openai/gpt-oss-20b",
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            logger.error("Groq package not installed. Install with: uv add groq")
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._fallback_response(prompt)
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            response = model.generate_content(
                f"{self._get_system_prompt()}\n\n{prompt}"
            )
            
            return response.text
            
        except ImportError:
            logger.error("Google Generative AI package not installed. Install with: uv add google-generativeai")
            return self._fallback_response(prompt)
    
    def _call_azure_openai(self, prompt: str) -> str:
        """Call Azure OpenAI API for prompt enrichment."""
        try:
            from openai import AzureOpenAI
            
            # Use the correct environment variable name
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            if not api_key:
                raise ValueError("AZURE_OPENAI_API_KEY not found in environment variables")
            
            client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=self.endpoint_url
            )
            
            # Use gpt-4o for prompt enrichment (more powerful and accurate)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a medical knowledge enrichment specialist. Your task is to enhance medical questions with relevant information from medical sources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent enrichment
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            logger.error("OpenAI package not installed. Install with: uv add openai")
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {e}")
            return self._fallback_response(prompt)
    
    def _call_huggingface(self, prompt: str) -> str:
        """Call HuggingFace Inference API."""
        try:
            import requests
            
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            payload = {
                "inputs": f"{self._get_system_prompt()}\n\n{prompt}",
                "parameters": {
                    "max_new_tokens": 1000,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            response = requests.post(
                "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()[0]["generated_text"]
            else:
                logger.error(f"HuggingFace API error: {response.status_code}")
                return self._fallback_response(prompt)
                
        except ImportError:
            logger.error("Requests package not installed. Install with: uv add requests")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when LLM is not available."""
        return f"""Based on the retrieved medical knowledge, here's what I can tell you:

{prompt}

Note: This is a fallback response. For more detailed and accurate medical information, please ensure your LLM API keys are properly configured in the .env file.

Remember: This information is for educational purposes only and should not replace professional medical advice."""
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for MedBot."""
        return """You are MedBot, an AI-powered healthcare assistant. Your purpose is to assist users only with healthcare, mental health, psychiatry, medical conditions, symptoms, treatments, anatomy, and evidence-based medical knowledge.

IMPORTANT RULES:
1. Only answer healthcare-related questions
2. If the query is non-medical, politely reject it
3. Always maintain empathetic, professional, and easy-to-understand explanations
4. Provide clear, structured answers with bullet points when appropriate
5. Do not provide personal medical diagnosis or prescriptions
6. Always add: "This is not a substitute for professional medical advice. Please consult a qualified healthcare provider."
7. Keep responses factually correct and aligned with evidence-based medicine
8. Use the retrieved medical knowledge to provide accurate, source-based information"""

class RAGSystem:
    """
    Complete RAG (Retrieval-Augmented Generation) system that implements
    the entire workflow from the diagram:
    
    1. Source Documents → Chunking Process → Text Chunks
    2. Text Chunks → Convert Docs to Embeddings → Embeddings
    3. Embeddings → Chroma DB Vector Index
    4. User Question → Embedding User Question → Embedded Questions
    5. Embedded Questions → Semantic Similarity Search → N-Relevant Chunks
    6. N-Relevant Chunks + User Question → Prompt → Generate Response (LLM)
    """
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        
        # Initialize components
        self.pdf_processor = PDFProcessor(chunk_size, chunk_overlap)
        self.embedding_system = EmbeddingSystem(embedding_model)
        self.llm_provider = LLMProvider()
        
        # Knowledge base status
        self.knowledge_base_initialized = False
        self.total_chunks = 0
        self.total_embeddings = 0
        
        # Auto-detect existing knowledge base
        self._auto_detect_knowledge_base()
        
        logger.info("RAG System initialized successfully")
    
    def _auto_detect_knowledge_base(self):
        """Automatically detect if knowledge base already exists and load it."""
        try:
            vector_info = self.embedding_system.get_vector_store_info()
            
            if vector_info.get('total_embeddings', 0) > 0:
                logger.info("Existing knowledge base detected! Loading...")
                
                # Update status to reflect existing knowledge base
                self.knowledge_base_initialized = True
                self.total_embeddings = vector_info.get('total_embeddings', 0)
                
                # Estimate total chunks (roughly 1:1 ratio with embeddings)
                self.total_chunks = self.total_embeddings
                
                logger.info(f"Knowledge base loaded successfully!")
                logger.info(f"   Total embeddings: {self.total_embeddings}")
                logger.info(f"   Estimated chunks: {self.total_chunks}")
                logger.info(f"   Vector store: {vector_info.get('status', 'unknown')}")
                
            else:
                logger.info("No existing knowledge base found. Run initialize_knowledge_base() to create one.")
                
        except Exception as e:
            logger.warning(f"Could not auto-detect knowledge base: {e}")
            logger.info("Run initialize_knowledge_base() to create or reinitialize the knowledge base.")
    
    def initialize_knowledge_base(self, med_books_directory: str = "med-books") -> bool:
        """
        Initialize the complete knowledge base from medical PDF documents.
        This implements the left side of the RAG workflow diagram.
        """
        logger.info("Initializing medical knowledge base...")
        
        try:
            # Step 1: Process PDFs and create chunks
            logger.info("Step 1: Processing PDFs and creating chunks...")
            chunks = self.pdf_processor.process_pdf_directory(med_books_directory)
            
            if not chunks:
                logger.error("No chunks created from PDFs")
                return False
            
            # Get chunk statistics
            stats = self.pdf_processor.get_chunk_statistics(chunks)
            logger.info(f"Chunk Statistics: {json.dumps(stats, indent=2)}")
            
            # Step 2: Create embeddings and store in vector database
            logger.info("Step 2: Creating embeddings and storing in vector database...")
            success = self.embedding_system.process_and_store_chunks(chunks)
            
            if not success:
                logger.error("Failed to process and store chunks")
                return False
            
            # Update status
            self.knowledge_base_initialized = True
            self.total_chunks = len(chunks)
            
            # Get vector store info
            vector_info = self.embedding_system.get_vector_store_info()
            self.total_embeddings = vector_info.get('total_embeddings', 0)
            
            logger.info(f"Knowledge base initialized successfully!")
            logger.info(f"   Total chunks: {self.total_chunks}")
            logger.info(f"   Total embeddings: {self.total_embeddings}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {e}")
            return False
    
    def query_knowledge_base(self, user_question: str, top_k: int = 5, llm_provider: str = None) -> Dict[str, Any]:
        """
        Query the knowledge base using RAG techniques.
        This implements the right side of the RAG workflow diagram.
        """
        if not self.knowledge_base_initialized:
            return {
                "success": False,
                "error": "Knowledge base not initialized",
                "suggestion": "Run initialize_knowledge_base() first"
            }
        
        # Step 0: Healthcare Query Filtering
        if not self._is_healthcare_query(user_question):
            return {
                "success": False,
                "error": "Non-healthcare query detected",
                "message": "⚠️ I can only provide information about healthcare and medical topics. Please ask me about health, symptoms, treatments, or medical conditions.",
                "question": user_question
            }
        
        try:
            logger.info(f"Processing healthcare question: {user_question[:100]}...")
            
            # Step 1: Embed the user question
            logger.info("Step 1: Embedding user question...")
            # (This is handled internally by the embedding system)
            
            # Step 2: Perform semantic similarity search
            logger.info("Step 2: Performing semantic similarity search...")
            relevant_chunks = self.embedding_system.search_similar_chunks(user_question, top_k)
            
            if not relevant_chunks:
                return {
                    "success": False,
                    "error": "No relevant information found",
                    "message": "I couldn't find specific information about that in my medical knowledge base. Please try rephrasing your question or ask about a different medical topic.",
                    "question": user_question
                }
            
            # Step 3: Prepare context for LLM
            logger.info("Step 3: Preparing context for LLM...")
            context = self._prepare_context(relevant_chunks)
            
            # Step 4: Generate response using LLM
            logger.info("Step 4: Generating response using LLM...")
            response = self._generate_llm_response(user_question, context, relevant_chunks, llm_provider)
            
            return {
                "success": True,
                "question": user_question,
                "response": response,
                "relevant_chunks": relevant_chunks,
                "context_length": len(context),
                "chunks_used": len(relevant_chunks),
                "llm_provider": llm_provider or self.llm_provider.default_provider
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return {
                "success": False,
                "error": str(e),
                "question": user_question
            }
    
    def _prepare_context(self, relevant_chunks: List[Dict]) -> str:
        """
        Prepare context from relevant chunks for the LLM.
        This implements the "Prompt Construction" part of the workflow.
        """
        context_parts = []
        
        for i, chunk in enumerate(relevant_chunks):
            source = chunk['metadata']['source']
            similarity = chunk['similarity_score']
            
            context_part = f"""
--- Source {i+1}: {source} (Relevance: {similarity:.2f}) ---
{chunk['content']}
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _is_healthcare_query(self, query: str) -> bool:
        """Check if the query is healthcare-related."""
        query_lower = query.lower()
        
        # Debug logging
        logger.info(f"🔍 Checking if query is healthcare-related: '{query}' -> '{query_lower}'")
        
        # Comprehensive healthcare keywords
        healthcare_keywords = [
            # Basic medical terms
            'health', 'medical', 'medicine', 'doctor', 'hospital', 'clinic',
            'symptom', 'disease', 'condition', 'treatment', 'therapy',
            'pain', 'fever', 'headache', 'nausea', 'fatigue', 'cough',
            'diabetes', 'hypertension', 'cancer', 'heart', 'lung', 'brain',
            'blood', 'infection', 'virus', 'bacteria', 'allergy',
            'mental', 'psychology', 'psychiatry', 'depression', 'anxiety',
            'pregnancy', 'childbirth', 'pediatric', 'elderly', 'geriatric',
            'surgery', 'medication', 'prescription', 'diagnosis', 'prognosis',
            
            # Medical specialties and fields
            'radiology', 'microbiology', 'pathology', 'immunology', 'oncology',
            'cardiology', 'neurology', 'dermatology', 'orthopedics', 'ophthalmology',
            'gynecology', 'urology', 'endocrinology', 'gastroenterology', 'pulmonology',
            'hematology', 'nephrology', 'rheumatology', 'dermatology', 'psychiatry',
            'pediatrics', 'geriatrics', 'emergency medicine', 'family medicine',
            
            # Scientific and medical disciplines
            'biology', 'biochemistry', 'biotechnology', 'genetics', 'genomics',
            'pharmacology', 'toxicology', 'epidemiology', 'biostatistics', 'anatomy',
            'physiology', 'histology', 'cytology', 'molecular biology', 'cell biology',
            'immunology', 'virology', 'bacteriology', 'parasitology', 'mycology',
            
            # Medical procedures and tests
            'x-ray', 'mri', 'ct scan', 'ultrasound', 'biopsy', 'surgery',
            'endoscopy', 'colonoscopy', 'mammogram', 'pap smear', 'blood test',
            'urine test', 'stool test', 'culture', 'sensitivity test',
            
            # Body systems and organs
            'cardiovascular', 'respiratory', 'digestive', 'nervous', 'endocrine',
            'musculoskeletal', 'integumentary', 'lymphatic', 'urinary', 'reproductive',
            'immune', 'skeletal', 'muscular', 'circulatory', 'respiratory',
            
            # Common medical conditions
            'inflammation', 'tumor', 'lesion', 'ulcer', 'abscess', 'cyst',
            'fracture', 'sprain', 'strain', 'arthritis', 'osteoporosis',
            'asthma', 'bronchitis', 'pneumonia', 'tuberculosis', 'emphysema',
            'hypertension', 'atherosclerosis', 'arrhythmia', 'myocardial infarction',
            'stroke', 'seizure', 'migraine', 'epilepsy', 'alzheimer', 'parkinson',
            'diabetes', 'obesity', 'thyroid', 'adrenal', 'pituitary',
            
            # Medical terminology
            'acute', 'chronic', 'benign', 'malignant', 'metastasis', 'remission',
            'prognosis', 'etiology', 'pathogenesis', 'morbidity', 'mortality',
            'incidence', 'prevalence', 'epidemic', 'pandemic', 'outbreak'
        ]
        
        # Check for healthcare keywords
        for keyword in healthcare_keywords:
            if keyword in query_lower:
                logger.info(f"✅ Healthcare keyword detected: '{keyword}' in query")
                return True
        
        # Check for medical question patterns
        medical_patterns = [
            'how to treat', 'symptoms of', 'causes of',
            'treatment for', 'medicine for', 'pain in', 'sick with',
            'diagnosed with', 'suffering from', 'experiencing',
            'how does', 'why do', 'when to',
            'definition of', 'meaning of', 'types of', 'kinds of',
            'examples of', 'signs of', 'indicators of', 'risk factors',
            'complications of', 'side effects of', 'prevention of'
        ]
        
        # Check for medical "what is" patterns (more specific)
        medical_what_patterns = [
            'what is diabetes', 'what is cancer', 'what is hypertension',
            'what is microbiology', 'what is radiology', 'what is pathology',
            'what is immunology', 'what is cardiology', 'what is neurology',
            'what is anatomy', 'what is physiology', 'what is biochemistry',
            'what is genetics', 'what is pharmacology', 'what is epidemiology',
            'what is virology', 'what is bacteriology', 'what is parasitology',
            'what is mycology', 'what is inflammation', 'what is tumor',
            'what is arthritis', 'what is asthma', 'what is stroke',
            'what is diabetes', 'what is obesity', 'what is thyroid'
        ]
        
        for pattern in medical_what_patterns:
            if pattern in query_lower:
                logger.info(f"✅ Medical 'what is' pattern detected: '{pattern}' in query")
                return True
        
        for pattern in medical_patterns:
            if pattern in query_lower:
                logger.info(f"✅ Medical pattern detected: '{pattern}' in query")
                return True
        
        # Check for common medical prefixes and suffixes
        medical_affixes = [
            'bio', 'micro', 'macro', 'endo', 'exo', 'hyper', 'hypo',
            'anti', 'pre', 'post', 'sub', 'super', 'ultra', 'multi',
            'itis', 'osis', 'emia', 'oma', 'pathy', 'algia', 'plegia',
            'rrhagia', 'rrhea', 'stenosis', 'ectasia', 'megaly', 'penia'
        ]
        
        for affix in medical_affixes:
            if affix in query_lower:
                logger.info(f"✅ Medical affix detected: '{affix}' in query")
                return True
        
        # Check for single-word medical queries (common medical terms)
        single_word_medical = [
            'microbiology', 'biology', 'radiology', 'pathology', 'immunology',
            'oncology', 'cardiology', 'neurology', 'dermatology', 'orthopedics',
            'ophthalmology', 'gynecology', 'urology', 'endocrinology',
            'gastroenterology', 'pulmonology', 'hematology', 'nephrology',
            'rheumatology', 'psychiatry', 'pediatrics', 'geriatrics',
            'anatomy', 'physiology', 'biochemistry', 'genetics', 'pharmacology',
            'epidemiology', 'virology', 'bacteriology', 'parasitology', 'mycology'
        ]
        
        # Remove spaces and check if it's a single medical term
        query_clean = query_lower.replace(' ', '').replace('-', '')
        for term in single_word_medical:
            if term in query_clean:
                logger.info(f"✅ Single medical term detected: '{term}' in query")
                return True
        
        logger.info(f"❌ Query '{query}' not detected as healthcare-related")
        return False
    
    def _generate_llm_response(self, question: str, context: str, relevant_chunks: List[Dict], llm_provider: str = None) -> str:
        """
        Generate response using Azure API for prompt enrichment + Groq API for final response.
        This implements the "Generate Response (LLM)" part of the workflow.
        """
        
        # Prepare the rich prompt for the LLM
        sources = list(set(chunk['metadata']['source'] for chunk in relevant_chunks))
        
        # Step 1: Use Azure API to enrich the prompt with retrieved information
        enriched_prompt = self._enrich_prompt_with_azure(question, context, relevant_chunks)
        
        # Log the enhanced prompt for debugging
        logger.info(f"Enhanced prompt created by Azure:")
        logger.info(f"Length: {len(enriched_prompt)} characters")
        logger.info(f"Preview: {enriched_prompt[:200]}...")
        
        # Step 2: Use Groq API with enriched prompt for final response
        try:
            logger.info("Calling Groq API with enhanced prompt...")
            response = self.llm_provider.generate_response(enriched_prompt, "groq")
            
            # Add source citations if not already included
            if not any(source in response for source in sources):
                response += f"\n\n**Sources:**\n"
                for source in sources:
                    response += f"- {source}\n"
            
            # Add medical disclaimer if not already included
            disclaimer = "\n\n⚠️ **IMPORTANT DISCLAIMER:** This information is for educational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare professional for diagnosis, treatment, and medical decisions."
            
            if disclaimer not in response:
                response += disclaimer
            
            # Add the enhanced prompt to the response for transparency
            full_response = f"""**ENHANCED PROMPT (Generated by Azure):**
{enriched_prompt}

**FINAL RESPONSE (Generated by Groq):**
{response}"""
            
            return full_response
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fallback to structured response
            return self._generate_fallback_response(question, context, relevant_chunks)
    
    def _enrich_prompt_with_azure(self, question: str, context: str, relevant_chunks: List[Dict]) -> str:
        """Use Azure API to enrich the prompt with retrieved medical knowledge."""
        try:
            sources = list(set(chunk['metadata']['source'] for chunk in relevant_chunks))
            
            # Create the enrichment prompt for Azure
            enrichment_prompt = f"""You are a medical knowledge enrichment specialist. Your task is to enhance a user's medical question with relevant information from medical sources.

User Question: {question}

Retrieved Medical Knowledge:
{context}

Your task: Analyze the retrieved medical knowledge and create an enriched, comprehensive prompt that:
1. Restates the user's question clearly
2. Integrates the most relevant medical information from the sources
3. Highlights key medical concepts, symptoms, treatments, or causes
4. Structures the information in a logical, medical-professional format
5. Maintains accuracy and medical terminology
6. Prepares this enriched context for a final medical AI response

Create a comprehensive, enriched prompt that combines the user's question with the retrieved medical knowledge in a way that will help generate the most accurate and helpful medical response."""

            # Use Azure API to enrich the prompt
            enriched_prompt = self.llm_provider._call_azure_openai(enrichment_prompt)
            
            # If Azure fails, return the original enriched prompt
            if not enriched_prompt or "error" in enriched_prompt.lower():
                logger.warning("Azure API enrichment failed, using fallback enrichment")
                return self._create_fallback_enriched_prompt(question, context, relevant_chunks)
            
            return enriched_prompt
            
        except Exception as e:
            logger.error(f"Error enriching prompt with Azure: {e}")
            return self._create_fallback_enriched_prompt(question, context, relevant_chunks)
    
    def _create_fallback_enriched_prompt(self, question: str, context: str, relevant_chunks: List[Dict]) -> str:
        """Create a fallback enriched prompt when Azure API is not available."""
        sources = list(set(chunk['metadata']['source'] for chunk in relevant_chunks))
        
        return f"""Based on comprehensive medical knowledge analysis, here is an enriched medical query:

ORIGINAL QUESTION: {question}

ENRICHED MEDICAL CONTEXT:
The user is seeking information about a medical condition, symptom, treatment, or health concern. Based on the retrieved medical knowledge from {len(sources)} authoritative sources including {', '.join(sources[:3])}, we have identified relevant medical information that addresses this query.

RETRIEVED MEDICAL KNOWLEDGE:
{context}

ENRICHED PROMPT FOR MEDICAL AI:
Please provide a comprehensive, evidence-based medical response to: "{question}"

Use the retrieved medical knowledge above to:
1. Provide a clear, accurate medical explanation
2. Include relevant symptoms, causes, treatments, or preventive measures
3. Reference the medical sources appropriately
4. Maintain professional medical terminology while being understandable
5. Include important medical warnings and considerations
6. Structure the response in a logical, medical-professional format

This enriched context combines the user's specific question with verified medical knowledge from authoritative sources to ensure the most accurate and helpful response possible."""
    
    def _generate_fallback_response(self, question: str, context: str, relevant_chunks: List[Dict]) -> str:
        """Generate fallback response when LLM fails."""
        sources = list(set(chunk['metadata']['source'] for chunk in relevant_chunks))
        
        response = f"""Based on the medical knowledge base, here's what I found regarding your question:

**Question:** {question}

**Response:**
I've found relevant information from {len(relevant_chunks)} medical sources that address your question. The information comes from the following medical documents: {', '.join(sources)}.

**Key Information:**
{context[:1000]}...

**Sources:**
"""
        
        for chunk in relevant_chunks:
            source = chunk['metadata']['source']
            relevance = chunk['similarity_score']
            response += f"- {source} (Relevance: {relevance:.2f})\n"
        
        response += """

**Note:** This response is generated using Retrieval-Augmented Generation (RAG) technology, which combines your question with relevant medical knowledge from the provided documents. For medical advice, always consult with qualified healthcare professionals.

⚠️ **IMPORTANT DISCLAIMER:** This information is for educational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare professional for diagnosis, treatment, and medical decisions."""
        
        return response
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the RAG system."""
        vector_info = self.embedding_system.get_vector_store_info()
        
        return {
            "rag_system_status": "active" if self.knowledge_base_initialized else "not_initialized",
            "knowledge_base_initialized": self.knowledge_base_initialized,
            "total_chunks": self.total_chunks,
            "total_embeddings": self.total_embeddings,
            "vector_store": vector_info,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "embedding_model": self.embedding_model
        }
    
    def reset_system(self) -> bool:
        """Reset the entire RAG system."""
        try:
            success = self.embedding_system.reset_knowledge_base()
            if success:
                self.knowledge_base_initialized = False
                self.total_chunks = 0
                self.total_embeddings = 0
                logger.info("RAG system reset successfully")
                return True
            else:
                logger.error("Failed to reset knowledge base")
                return False
        except Exception as e:
            logger.error(f"Error resetting system: {e}")
            return False
    
    def add_documents(self, pdf_directory: str) -> bool:
        """
        Add new documents to the existing knowledge base.
        This allows incremental updates to the knowledge base.
        """
        logger.info(f"Adding new documents from {pdf_directory}...")
        
        try:
            # Process new PDFs
            new_chunks = self.pdf_processor.process_pdf_directory(pdf_directory)
            
            if not new_chunks:
                logger.warning("No new chunks created")
                return False
            
            # Add to existing knowledge base
            success = self.embedding_system.process_and_store_chunks(new_chunks)
            
            if success:
                self.total_chunks += len(new_chunks)
                vector_info = self.embedding_system.get_vector_store_info()
                self.total_embeddings = vector_info.get('total_embeddings', 0)
                
                logger.info(f"Added {len(new_chunks)} new chunks to knowledge base")
                return True
            else:
                logger.error("Failed to add new chunks")
                return False
                
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def get_context_only(self, question: str) -> Dict[str, Any]:
        """Get only the RAG context without generating a response."""
        try:
            if not self.knowledge_base_initialized:
                return {
                    "success": False,
                    "error": "Knowledge base not initialized"
                }
            
            # Get relevant chunks
            relevant_chunks = self.embedding_system.search_similar_chunks(question, top_k=5)
            
            if not relevant_chunks:
                return {
                    "success": False,
                    "error": "No relevant context found"
                }
            
            return {
                "success": True,
                "relevant_chunks": relevant_chunks,
                "total_chunks_found": len(relevant_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error getting context only: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_azure_enhanced_response(self, question: str, user_name: str = None) -> Dict[str, Any]:
        """Generate comprehensive response using Azure OpenAI with RAG context and user personalization."""
        try:
            if not self.knowledge_base_initialized:
                return {
                    "success": False,
                    "error": "Knowledge base not initialized"
                }
            
            # Get relevant chunks
            relevant_chunks = self.embedding_system.search_similar_chunks(question, top_k=5)
            
            if not relevant_chunks:
                return {
                    "success": False,
                    "error": "No relevant context found"
                }
            
            # Create context from chunks
            context = self._prepare_context(relevant_chunks)
            
            # Generate comprehensive response using Azure with user personalization
            comprehensive_prompt = self._create_comprehensive_prompt(question, context, user_name)
            
            try:
                azure_response = self.llm_provider._call_azure_openai(comprehensive_prompt)
                
                return {
                    "success": True,
                    "response": azure_response,
                    "relevant_chunks": relevant_chunks,
                    "chunks_used": len(relevant_chunks),
                    "context_used": context[:500] + "..." if len(context) > 500 else context,
                    "user_name": user_name
                }
                
            except Exception as e:
                logger.error(f"Azure OpenAI error: {e}")
                # Fallback to regular response
                fallback_response = self._generate_fallback_response(question, context, relevant_chunks, user_name)
                return {
                    "success": True,
                    "response": fallback_response,
                    "relevant_chunks": relevant_chunks,
                    "chunks_used": len(relevant_chunks),
                    "context_used": context[:500] + "..." if len(context) > 500 else context,
                    "note": "Azure OpenAI unavailable, using fallback response",
                    "user_name": user_name
                }
                
        except Exception as e:
            logger.error(f"Error generating Azure enhanced response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_user_name(self, question: str) -> str:
        """Extract user name from the question if present."""
        import re
        
        # Common patterns for name introduction
        name_patterns = [
            r"i am (\w+)",
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)",
            r"this is (\w+)",
            r"(\w+) here",
            r"(\w+) speaking"
        ]
        
        question_lower = question.lower()
        
        for pattern in name_patterns:
            match = re.search(pattern, question_lower)
            if match:
                name = match.group(1).capitalize()
                logger.info(f"👤 User name extracted: {name}")
                return name
        
        return None
    
    def _generate_fallback_response(self, question: str, context: str, relevant_chunks: List[Dict], user_name: str = None) -> str:
        """Generate fallback response when LLM fails, with user personalization."""
        sources = list(set(chunk['metadata']['source'] for chunk in relevant_chunks))
        
        # Personalize the response if user name is available
        greeting = f"Hello {user_name}! " if user_name else ""
        
        response = f"""{greeting}Based on the medical knowledge base, here's what I found regarding your question:

**Question:** {question}

**Response:**
I've found relevant information from {len(relevant_chunks)} medical sources that address your question. The information comes from the following medical documents: {', '.join(sources)}.

**Key Information:**
{context[:1000]}...

**Sources:**
"""
        
        for chunk in relevant_chunks:
            source = chunk['metadata']['source']
            relevance = chunk['similarity_score']
            response += f"- {source} (Relevance: {relevance:.2f})\n"
        
        response += f"""

**Note:** This response is generated using Retrieval-Augmented Generation (RAG) technology, which combines your question with relevant medical knowledge from the provided documents. For medical advice, always consult with qualified healthcare professionals.

⚠️ **IMPORTANT DISCLAIMER:** This information is for educational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare professional for diagnosis, treatment, and medical decisions."""
        
        return response
    
    def _create_comprehensive_prompt(self, question: str, context: str, user_name: str = None) -> str:
        """Create a comprehensive prompt for Azure OpenAI with user personalization."""
        
        # Personalize the prompt if user name is available
        personalization = f"Hello {user_name}! " if user_name else ""
        
        return f"""{personalization}You are a medical AI specialist. Use the following medical context to provide a comprehensive, well-structured response to the user's question.

**USER QUESTION:** {question}

**MEDICAL CONTEXT (RAG System):**
{context}

**INSTRUCTIONS:**
Create a massive, well-explained, and structured medical response that covers:

1. **Definition and Overview** - Clear explanation of the medical concept with layman's terms
2. **Causes and Risk Factors** - Detailed analysis of contributing factors and epidemiology
3. **Symptoms and Clinical Presentation** - Comprehensive symptom description with severity levels
4. **Diagnosis and Testing** - Available diagnostic methods, procedures, and what to expect
5. **Treatment Options** - Current treatment approaches, medications, therapies, and alternatives
6. **Prevention and Management** - Preventive measures, lifestyle changes, and ongoing care
7. **Prognosis and Outlook** - Expected outcomes, recovery time, and long-term considerations
8. **Additional Resources** - Where to find more information, support groups, and specialists
9. **When to Seek Medical Help** - Red flags, emergency symptoms, and urgency indicators
10. **Patient Education** - Self-care tips, monitoring, and follow-up recommendations

**RESPONSE REQUIREMENTS:**
- Use the provided medical context as your foundation and expand significantly
- Include relevant medical terminology with clear explanations
- Provide actionable insights and evidence-based recommendations
- Cite the sources appropriately and mention their reliability
- Structure the response with clear headings and bullet points
- Make the response comprehensive, educational, and easy to understand
- Include practical examples and real-world applications
- Address common misconceptions and concerns
- Provide both immediate and long-term perspectives
- Format using markdown for optimal readability

**PERSONALIZATION:**
- If the user provided their name, address them personally
- Make the response feel conversational and caring
- Consider the user's level of medical knowledge
- Provide encouragement and positive reinforcement

Ensure the response is comprehensive, accurate, and provides immense value to the user while maintaining a warm, professional tone."""
