import os
import asyncio
import json
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from pathlib import Path
import logging
import re

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

# Pydantic models for request/response
class ChatRequest(BaseModel):
    user_question: str
    chat_history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[Dict[str, Any]]] = []
    status: str = "success"

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

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint for processing user questions."""
    try:
        # Process the user question through the RAG system
        rag_response = rag_system.generate_azure_enhanced_response(
            question=request.user_question,
            chat_history=request.chat_history
        )
        
        # Check if the response was successful
        if not rag_response.get("success", False):
            error_msg = rag_response.get("error", "Unknown error occurred")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Extract the response text and sources
        response_text = rag_response.get("response", "No response generated")
        relevant_chunks = rag_response.get("relevant_chunks", [])
        
        # Clean the response text to remove any HTML tags
        response_text = re.sub(r'<[^>]+>', '', response_text)
        response_text = response_text.strip()
        
        # Add a note to encourage table usage when appropriate
        if "table" not in response_text.lower() and len(response_text) > 500:
            response_text += "\n\n💡 **Tip:** For complex medical information, consider asking me to present data in tables for better understanding!"
        
        # Format sources for the frontend
        sources = []
        for chunk in relevant_chunks:
            source_info = {
                "source": chunk.get("metadata", {}).get("source", "Unknown Source"),
                "relevance_score": chunk.get("similarity_score", 0.0),
                "content": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", "")
            }
            sources.append(source_info)
        
        # Return the response
        return ChatResponse(
            response=response_text,
            sources=sources,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/test-rag")
async def test_rag():
    """Test endpoint to verify RAG system is working."""
    try:
        # Simple test query
        test_response = rag_system.generate_azure_enhanced_response(
            question="What is microbiology?",
            chat_history=[]
        )
        
        return {
            "status": "success",
            "rag_system_working": test_response.get("success", False),
            "test_response": test_response.get("response", "No response")[:200] + "..." if len(test_response.get("response", "")) > 200 else test_response.get("response", ""),
            "chunks_used": test_response.get("chunks_used", 0)
        }
        
    except Exception as e:
        logger.error(f"Error testing RAG system: {e}")
        return {
            "status": "error",
            "error": str(e),
            "rag_system_working": False
        }

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
