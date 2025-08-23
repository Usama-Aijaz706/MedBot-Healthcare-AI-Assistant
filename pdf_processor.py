import PyPDF2
import re
from typing import List, Dict, Optional
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Advanced PDF processor with intelligent chunking for medical documents.
    Implements the chunking process from the RAG workflow diagram.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF with enhanced cleaning for medical documents.
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        # Add page number for reference
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                logger.info(f"Extracted text from {pdf_path}: {len(text)} characters")
                return self._clean_text(text)
                
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text for better chunking and embedding.
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers (common in medical documents)
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'\d+/\d+', '', text)
        
        # Clean up medical abbreviations and formatting
        text = re.sub(r'([A-Z])\s*\.\s*([A-Z])', r'\1.\2', text)  # Fix abbreviations like "D R" -> "D.R"
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def create_intelligent_chunks(self, text: str, pdf_name: str) -> List[Dict[str, str]]:
        """
        Create intelligent chunks using advanced text splitting techniques.
        This implements the "Chunking Process" from the RAG workflow.
        """
        chunks = []
        
        # Split by sentences first (better for medical content)
        sentences = self._split_by_sentences(text)
        
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk.strip():
                    # Save current chunk
                    chunks.append({
                        'id': f"{pdf_name}_chunk_{chunk_id}",
                        'content': current_chunk.strip(),
                        'source': pdf_name,
                        'chunk_size': len(current_chunk.strip())
                    })
                    chunk_id += 1
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'id': f"{pdf_name}_chunk_{chunk_id}",
                'content': current_chunk.strip(),
                'source': pdf_name,
                'chunk_size': len(current_chunk.strip())
            })
        
        logger.info(f"Created {len(chunks)} chunks from {pdf_name}")
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using medical document-aware patterns.
        """
        # Split by sentence endings, but preserve medical abbreviations
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Handle medical abbreviations that might end with periods
        medical_abbrevs = ['Dr.', 'Mr.', 'Mrs.', 'Prof.', 'Ph.D.', 'M.D.', 'B.Sc.', 'M.Sc.']
        corrected_sentences = []
        
        for sentence in sentences:
            # Check if sentence ends with medical abbreviation
            if any(sentence.endswith(abbrev) for abbrev in medical_abbrevs):
                # Don't split on these
                corrected_sentences.append(sentence)
            else:
                corrected_sentences.append(sentence)
        
        return corrected_sentences
    
    def _get_overlap_text(self, text: str) -> str:
        """
        Get overlap text from the end of a chunk for continuity.
        """
        words = text.split()
        if len(words) <= self.chunk_overlap // 10:  # Approximate word count
            return text
        
        overlap_words = words[-(self.chunk_overlap // 10):]
        return " ".join(overlap_words)
    
    def process_pdf_directory(self, directory_path: str) -> List[Dict[str, str]]:
        """
        Process all PDFs in a directory and return all chunks.
        """
        pdf_dir = Path(directory_path)
        all_chunks = []
        
        if not pdf_dir.exists():
            logger.error(f"Directory {directory_path} does not exist")
            return all_chunks
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing {pdf_file.name}...")
                text = self.extract_text_from_pdf(str(pdf_file))
                
                if text:
                    chunks = self.create_intelligent_chunks(text, pdf_file.name)
                    all_chunks.extend(chunks)
                    logger.info(f"Successfully processed {pdf_file.name}: {len(chunks)} chunks")
                else:
                    logger.warning(f"No text extracted from {pdf_file.name}")
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                continue
        
        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks
    
    def get_chunk_statistics(self, chunks: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Get statistics about the created chunks.
        """
        if not chunks:
            return {}
        
        chunk_sizes = [chunk['chunk_size'] for chunk in chunks]
        sources = list(set(chunk['source'] for chunk in chunks))
        
        return {
            'total_chunks': len(chunks),
            'total_characters': sum(chunk_sizes),
            'average_chunk_size': sum(chunk_sizes) / len(chunks),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'unique_sources': len(sources),
            'sources': sources
        }

