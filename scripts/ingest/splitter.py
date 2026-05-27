"""Text splitting and chunking configurations for ingestion."""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def get_splitter(chunk_size: int = 900, chunk_overlap: int = 120) -> RecursiveCharacterTextSplitter:
    """Return a configured RecursiveCharacterTextSplitter for optimal semantic chunking.
    
    Args:
        chunk_size: Target character count per chunk.
        chunk_overlap: Overlap character count between consecutive chunks.
        
    Returns:
        A RecursiveCharacterTextSplitter instance.
    """
    logger.info("Initializing text splitter: chunk_size=%d, chunk_overlap=%d", chunk_size, chunk_overlap)
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
