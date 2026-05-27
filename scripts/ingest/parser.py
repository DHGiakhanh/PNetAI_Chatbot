"""Document parsers and text cleaning filters for PDF and JSON files."""

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Rigorous cleaning routine to strip noise, junk characters, and normalize whitespaces.
    
    Acts as the primary text filter to ensure high-quality semantic vector matching.
    """
    if not text:
        return ""
    
    # 1. Replace non-breaking spaces (\xa0) and carriage returns
    text = text.replace("\xa0", " ").replace("\r", "")
    
    # 2. Strip control / non-printable characters (except newline, tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", text)
    
    # 3. Strip HTML tags (if any exist in crawled JSON or converted blogs)
    text = re.sub(r"<[^>]+?>", "", text)
    
    # 4. Resolve hyphenated compound words split across newlines
    # Example: "vac-\nxin" -> "vac-xin" or "viêm -\n đường" -> "viêm đường"
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1-\2", text)
    
    # 5. Remove header / footer noise common in PDF extractions (e.g., URL watermarks, page markers)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Filter out obvious boilerplate, page numbers, or watermark URLs
        if not stripped:
            cleaned_lines.append("")
            continue
            
        # Patterns like: "Trang 1 / 15", "Page 2", "2vet.vn", "Bệnh viện thú y 2Vet"
        if re.search(r"^\s*trang\s*\d+\s*(?:/\s*\d+)?\s*$", stripped, re.IGNORECASE):
            continue
        if re.search(r"^\s*page\s*\d+\s*$", stripped, re.IGNORECASE):
            continue
        if "2vet.vn" in stripped.lower():
            continue
            
        cleaned_lines.append(stripped)
        
    text = "\n".join(cleaned_lines)
    
    # 6. Normalize multiple blank lines (max 2 consecutive newlines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # 7. Normalize horizontal spaces (tabs and multiple spaces to single space)
    text = re.sub(r"[ \t]+", " ", text)
    
    return text.strip()


def parse_json_faq(file_path: Path, splitter: Any, limit_json: int | None = None) -> list[dict[str, Any]]:
    """Parse JSON blog and FAQ files, apply text cleaning, and chunk them.
    
    Supports key schemas:
    - [{url, title, content, tag}] -> Article blog format
    """
    logger.info("[PARSE JSON] Starting ingestion parsing for file: %s", file_path.name)
    processed_docs = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    total_items = len(data)
    logger.info("[PARSE JSON] File contains %d total records in JSON array", total_items)
    
    parsed_count = 0
    for idx, item in enumerate(data, 1):
        if limit_json is not None and idx > limit_json:
            logger.info("[PARSE JSON] Reached limit of %d JSON records. Halting JSON parsing.", limit_json)
            break
            
        title = item.get("title", "").strip()
        content = item.get("content", "").strip()
        tag = item.get("tag", "").strip()
        
        # 1. Clean the text using the rigorous cleaning pipeline
        cleaned_content = clean_text(content)
        cleaned_title = clean_text(title)
        
        if not cleaned_content:
            continue
            
        # 2. Map Vietnamese species tags to English database keys
        species = "all"
        if "cho" in tag.lower():
            species = "dog"
        elif "meo" in tag.lower():
            species = "cat"
            
        # 3. Chunking phase
        chunks = splitter.split_text(cleaned_content)
        
        for chunk_idx, chunk_content in enumerate(chunks):
            chunk_title = cleaned_title if len(chunks) == 1 else f"{cleaned_title} (Phần {chunk_idx + 1})"
            
            processed_docs.append({
                "id_base": f"{file_path.stem}-item{idx}-c{chunk_idx}",
                "title": chunk_title,
                "content": chunk_content,
                "category": "healthcare",
                "species": species,
                "tags": ["bệnh chó mèo", "blog hỏi đáp", tag] if tag else ["bệnh chó mèo", "blog hỏi đáp"],
                "source": file_path.name,
                "page": 1
            })
        
        parsed_count += 1
        if parsed_count % 100 == 0 or parsed_count == min(total_items, limit_json or total_items):
            logger.info("[PARSE JSON] Processed, cleaned, and chunked: %d/%d entries", parsed_count, limit_json or total_items)
            
    logger.info("[PARSE JSON] Parsing complete. Generated %d chunks from %d JSON articles.", len(processed_docs), parsed_count)
    return processed_docs


def parse_pdf_disease_manual(file_path: Path, splitter: Any) -> list[dict[str, Any]]:
    """Parse PDF reference manuals page-by-page, extract clean text, and chunk it."""
    logger.info("[PARSE PDF] Starting ingestion parsing for file: %s", file_path.name)
    processed_chunks = []
    
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    logger.info("[PARSE PDF] File has %d pages to extract", total_pages)
    
    species = "dog" if "cho" in file_path.name.lower() else "cat" if "meo" in file_path.name.lower() else "all"
    
    parsed_pages = 0
    for page_idx, page in enumerate(reader.pages, 1):
        raw_text = page.extract_text()
        if not raw_text or not raw_text.strip():
            logger.debug("[PARSE PDF] Skipped page %d (empty or scanned image)", page_idx)
            continue
            
        # 1. Apply cleaning filters to remove page headers, footers, carriage returns, etc.
        cleaned_text = clean_text(raw_text)
        if not cleaned_text:
            continue
            
        # 2. Chunk the cleaned page content
        chunks = splitter.split_text(cleaned_text)
        
        for chunk_idx, chunk_content in enumerate(chunks):
            title = f"Cẩm nang Bệnh: {file_path.stem.replace('_', ' ').replace('-', ' ').title()} (Trang {page_idx})"
            
            processed_chunks.append({
                "id_base": f"{file_path.stem}-p{page_idx}-c{chunk_idx}",
                "title": title,
                "content": chunk_content,
                "category": "healthcare",
                "species": species,
                "tags": ["bệnh chó mèo", "cẩm nang điều trị", file_path.stem],
                "source": file_path.name,
                "page": page_idx
            })
            
        parsed_pages += 1
        if parsed_pages % 20 == 0 or parsed_pages == total_pages:
            logger.info("[PARSE PDF] Processed and cleaned page: %d/%d", page_idx, total_pages)
            
    logger.info("[PARSE PDF] Parsing complete. Generated %d chunks from %d pages.", len(processed_chunks), parsed_pages)
    return processed_chunks
