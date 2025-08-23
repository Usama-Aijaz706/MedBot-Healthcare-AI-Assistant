import os
import asyncio
import json
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from pathlib import Path
import logging

# Import our RAG system
from rag_system import RAGSystem
from chat_interface import ChatInterface

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MedBot - RAG-Enhanced Healthcare AI Assistant",
    description="An intelligent healthcare chatbot powered by RAG technology",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize RAG system and chat interface
rag_system = RAGSystem()
chat_interface = ChatInterface(healthcare_rag=None)  # We don't need the old RAG system

# Global variables for system status
knowledge_base_initialized = False
system_status = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    global knowledge_base_initialized, system_status
    
    logger.info("🚀 Starting MedBot RAG-Enhanced Healthcare AI Assistant...")
    
    # Check if knowledge base exists
    if os.path.exists("./healthcare_knowledge_db"):
        logger.info("📚 Found existing knowledge base, loading...")
        try:
            # Try to get system status to see if it's working
            status = rag_system.get_system_status()
            if status.get('rag_system_status') == 'active':
                knowledge_base_initialized = True
                system_status = status
                logger.info("✅ Existing knowledge base loaded successfully")
            else:
                logger.info("⚠️ Existing knowledge base found but not active, will reinitialize")
        except Exception as e:
            logger.warning(f"⚠️ Error loading existing knowledge base: {e}")
    
    system_status = rag_system.get_system_status()
    
    # Show startup information
    logger.info("🏥 MedBot is ready!")
    logger.info("📚 Found medical PDFs in med-books/ directory")
    logger.info("🔍 Use the web interface to initialize the knowledge base")
    logger.info("🌐 Open http://localhost:8000 in your browser")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "MedBot RAG-Enhanced Healthcare AI Assistant",
        "knowledge_base_initialized": knowledge_base_initialized
    }

@app.get("/status")
async def get_status():
    """Get comprehensive system status."""
    global system_status
    system_status = rag_system.get_system_status()
    return system_status

@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """Chat endpoint for the RAG-enhanced chatbot."""
    global knowledge_base_initialized, system_status
    
    try:
        user_message = request.get("message", "").strip()
        chat_mode = request.get("mode", "rag")  # "rag" or "general"
        get_context_only = request.get("get_context_only", False)
        use_azure_enhancement = request.get("use_azure_enhancement", False)
        generate_comprehensive_response = request.get("generate_comprehensive_response", False)
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"💬 Chat request: {chat_mode} mode - {user_message[:100]}...")
        
        # Check if only context is needed
        if get_context_only:
            if not knowledge_base_initialized:
                return {
                    "success": False,
                    "error": "Knowledge base not initialized",
                    "suggestion": "Please wait for initialization to complete"
                }
            
            # Get only RAG context without generating response
            context_response = rag_system.get_context_only(user_message)
            if context_response["success"]:
                return {
                    "success": True,
                    "relevant_chunks": context_response["relevant_chunks"],
                    "sources": [{"source": chunk["metadata"]["source"], "relevance": chunk["similarity_score"]} for chunk in context_response["relevant_chunks"]],
                    "mode": "context_only"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to retrieve context",
                    "details": context_response.get("error", "Unknown error")
                }
        
        # Check if Azure enhancement is requested
        if use_azure_enhancement and generate_comprehensive_response:
            if not knowledge_base_initialized:
                return {
                    "success": False,
                    "error": "Knowledge base not initialized",
                    "suggestion": "Please wait for initialization to complete"
                }
            
            # Extract user name if present in the message
            user_name = rag_system.extract_user_name(user_message)
            
            # Use Azure to generate comprehensive response with user personalization
            azure_response = rag_system.generate_azure_enhanced_response(user_message, user_name)
            if azure_response["success"]:
                return {
                    "success": True,
                    "response": azure_response["response"],
                    "sources": [{"source": chunk["metadata"]["source"], "relevance": chunk["similarity_score"]} for chunk in azure_response.get("relevant_chunks", [])],
                    "mode": "azure_enhanced",
                    "chunks_used": azure_response.get("chunks_used", 0),
                    "user_name": user_name
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate Azure enhanced response",
                    "details": azure_response.get("error", "Unknown error")
                }
        
        if chat_mode == "rag":
            if not knowledge_base_initialized:
                # Try to initialize knowledge base if not done
                logger.info("🔄 Knowledge base not initialized, attempting to initialize...")
                success = rag_system.initialize_knowledge_base()
                if success:
                    knowledge_base_initialized = True
                    system_status = rag_system.get_system_status()
                else:
                    return {
                        "success": False,
                        "error": "Knowledge base not initialized. Please wait for initialization to complete.",
                        "suggestion": "Try again in a few moments or contact support."
                    }
            
            # Use RAG system for response
            response = rag_system.query_knowledge_base(user_message)
            
            if response["success"]:
                return {
                    "success": True,
                    "response": response["response"],
                    "sources": [{"source": chunk["metadata"]["source"], "relevance": chunk["similarity_score"]} for chunk in response["relevant_chunks"]],
                    "mode": "rag",
                    "chunks_used": response["chunks_used"]
                }
            else:
                # Fallback to general chat if RAG fails
                logger.warning(f"RAG query failed: {response.get('error')}, falling back to general chat")
                general_response = chat_interface.generate_response(user_message)
                return {
                    "success": True,
                    "response": general_response + "\n\n⚠️ Note: RAG system unavailable, using general knowledge.",
                    "sources": [],
                    "mode": "general_fallback",
                    "chunks_used": 0
                }
        else:
            # General chat mode
            response = chat_interface.generate_response(user_message)
            return {
                "success": True,
                "response": response,
                "sources": [],
                "mode": "general",
                "chunks_used": 0
            }
            
    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {e}")
        return {
            "success": False,
            "error": "An error occurred while processing your request",
            "details": str(e)
        }

@app.post("/api/initialize-knowledge-base")
async def initialize_knowledge_base_endpoint():
    """Initialize the knowledge base from medical PDFs."""
    try:
        logger.info("🔄 Manual knowledge base initialization requested...")
        
        success = rag_system.initialize_knowledge_base()
        
        if success:
            global knowledge_base_initialized, system_status
            knowledge_base_initialized = True
            system_status = rag_system.get_system_status()
            
            return {
                "success": True,
                "message": "Knowledge base initialized successfully",
                "status": system_status
            }
        else:
            return {
                "success": False,
                "error": "Failed to initialize knowledge base",
                "suggestion": "Check if PDF files exist in the med-books directory"
            }
            
    except Exception as e:
        logger.error(f"❌ Error initializing knowledge base: {e}")
        return {
            "success": False,
            "error": "An error occurred during initialization",
            "details": str(e)
        }

@app.post("/api/reset-knowledge-base")
async def reset_knowledge_base_endpoint():
    """Reset the knowledge base."""
    try:
        logger.info("🔄 Knowledge base reset requested...")
        
        success = rag_system.reset_system()
        
        if success:
            global knowledge_base_initialized, system_status
            knowledge_base_initialized = False
            system_status = rag_system.get_system_status()
            
            return {
                "success": True,
                "message": "Knowledge base reset successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to reset knowledge base"
            }
            
    except Exception as e:
        logger.error(f"❌ Error resetting knowledge base: {e}")
        return {
            "success": False,
            "error": "An error occurred during reset",
            "details": str(e)
        }

@app.get("/api/knowledge-base-info")
async def get_knowledge_base_info():
    """Get information about the knowledge base."""
    try:
        # Get PDF files info
        med_books_dir = Path("med-books")
        pdf_files = []
        
        if med_books_dir.exists():
            pdf_files = [f.name for f in med_books_dir.glob("*.pdf")]
        
        # Get system status
        status = rag_system.get_system_status()
        
        return {
            "success": True,
            "pdf_files": pdf_files,
            "total_pdfs": len(pdf_files),
            "system_status": status,
            "knowledge_base_initialized": knowledge_base_initialized
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting knowledge base info: {e}")
        return {
            "success": False,
            "error": "An error occurred while getting information",
            "details": str(e)
        }

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a new PDF to the med-books directory."""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Create med-books directory if it doesn't exist
        med_books_dir = Path("med-books")
        med_books_dir.mkdir(exist_ok=True)
        
        # Save the uploaded file
        file_path = med_books_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"📚 PDF uploaded successfully: {file.filename}")
        
        return {
            "success": True,
            "message": f"PDF '{file.filename}' uploaded successfully",
            "filename": file.filename,
            "file_path": str(file_path)
        }
        
    except Exception as e:
        logger.error(f"❌ Error uploading PDF: {e}")
        return {
            "success": False,
            "error": "An error occurred while uploading the PDF",
            "details": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
