import logging
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from .loader import DocumentLoader

logger = logging.getLogger(__name__)

class DischargeLoader:
    """
    Specialized loader for Discharge Instructions.
    
    It wraps the generic DocumentLoader but adds specific pre-processing 
    relevant to medical discharge summaries (e.g., handling specific formatting issues).
    """
    
    @staticmethod
    def load_discharge_summary(file_path: Path) -> str:
        """
        Load a discharge summary file and return the full text content.
        
        Args:
            file_path: Path to the discharge summary file (PDF, TXT, DOCX)
            
        Returns:
            The full text of the discharge summary.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        logger.info(f"Loading discharge summary from: {file_path}")
        
        # Use existing DocumentLoader to handle file formats
        docs = DocumentLoader.load_document(file_path)
        
        if not docs:
            logger.warning(f"No content extracted from {file_path}")
            return ""
            
        # Merge all pages into a single text block
        full_text = "\n\n".join([doc.page_content for doc in docs])
        
        # Basic cleanup (this can be expanded for specific EMR formats)
        cleaned_text = DischargeLoader._clean_text(full_text)
        
        return cleaned_text

    @staticmethod
    def _clean_text(text: str) -> str:
        """Basic text cleanup."""
        # Replace multiple newlines with double newline
        import re
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove common EMR headers/footers placeholders if found (very basic examples)
        # text = text.replace("Page [of]", "") 
        
        return text.strip()
