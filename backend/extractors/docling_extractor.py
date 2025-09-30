"""
Docling PDF Extraction Module
Handles PDF extraction using the Docling framework
"""

import io
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box coordinates for document elements"""
    x0: float
    y0: float
    x1: float
    y1: float
    page: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "page": self.page
        }


@dataclass
class ExtractedElement:
    """Represents an extracted document element"""
    type: str  # title, header, paragraph, table, figure
    content: str
    bbox: Optional[BoundingBox]
    page: int
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "page": self.page,
            "confidence": self.confidence
        }


class DoclingExtractor:
    """Docling-based PDF extraction"""
    
    def __init__(self):
        self.model_name = "docling"
        logger.info(f"Initializing {self.model_name} extractor")
    
    def extract(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract content from PDF using Docling
        
        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        start_time = time.time()
        
        try:
            # Import Docling (lazy import to avoid loading if not needed)
            from docling.document_converter import DocumentConverter
            
            logger.info(f"Starting Docling extraction for {filename}")
            
            # Initialize converter
            converter = DocumentConverter()
            
            import os
            import tempfile

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            try:
                tmp.write(pdf_bytes)
                tmp.close()  # Close so Docling can open it
                result = converter.convert(tmp.name)
            finally:
                os.unlink(tmp.name)  # Clean up the temp file
            # Note: Docling expects a file path, so we save bytes to a temp file
                        
            # Extract structured elements
            elements = self._parse_docling_output(result)
            
            # Generate markdown
            markdown = self._generate_markdown(elements)
            
            # Calculate statistics
            stats = self._calculate_stats(elements)
            
            processing_time = (time.time() - start_time) * 1000  # milliseconds
            
            return {
                "status": "success",
                "model": self.model_name,
                "filename": filename,
                "markdown": markdown,
                "elements": [e.to_dict() for e in elements],
                "statistics": stats,
                "processing_time_ms": round(processing_time, 2),
                "metadata": {
                    "total_pages": stats.get("total_pages", 1),
                    "total_elements": len(elements)
                }
            }
            
        except ImportError as e:
            logger.error(f"Docling not installed: {e}")
            return self._fallback_extraction(pdf_bytes, filename, start_time)
        except Exception as e:
            logger.error(f"Docling extraction failed: {e}")
            return self._fallback_extraction(pdf_bytes, filename, start_time)
    
    def _parse_docling_output(self, result) -> List[ExtractedElement]:
        """Parse Docling output into structured elements"""
        elements = []
        
        try:
            # Debug: log the raw result and document
            doc = getattr(result, 'document', None)
            if doc is not None:
                items = list(doc.iterate_items())
            else:
                logger.warning("Docling result has no document attribute!")
                return elements
            
            page_num = 1
            element_id = 0
            
            # Iterate through document elements
            for item in items:
                element_type = self._map_docling_type(getattr(item, 'label', 'paragraph'))
                
                # Extract text content
                content = item.text if hasattr(item, 'text') else str(item)
                
                # Extract bounding box if available
                bbox = None
                if hasattr(item, 'bbox') and item.bbox:
                    bbox = BoundingBox(
                        x0=item.bbox.l,
                        y0=item.bbox.t,
                        x1=item.bbox.r,
                        y1=item.bbox.b,
                        page=page_num
                    )
                
                element = ExtractedElement(
                    type=element_type,
                    content=content.strip(),
                    bbox=bbox,
                    page=page_num,
                    confidence=None  # Docling doesn't provide confidence scores
                )
                
                elements.append(element)
                element_id += 1
            
            logger.info(f"Parsed {len(elements)} elements from Docling output")
            
        except Exception as e:
            logger.error(f"Error parsing Docling output: {e}")
        
        return elements
    
    def _map_docling_type(self, docling_label: str) -> str:
        """Map Docling element types to our standard types"""
        mapping = {
            "title": "title",
            "heading": "header",
            "paragraph": "paragraph",
            "text": "paragraph",
            "table": "table",
            "figure": "figure",
            "list": "list",
            "caption": "caption"
        }
        return mapping.get(docling_label.lower(), "paragraph")
    
    def _generate_markdown(self, elements: List[ExtractedElement]) -> str:
        """Generate markdown from extracted elements"""
        markdown_parts = []
        
        for element in elements:
            if element.type == "title":
                markdown_parts.append(f"# {element.content}\n")
            elif element.type == "header":
                markdown_parts.append(f"## {element.content}\n")
            elif element.type == "paragraph":
                markdown_parts.append(f"{element.content}\n")
            elif element.type == "list":
                markdown_parts.append(f"- {element.content}\n")
            elif element.type == "table":
                markdown_parts.append(f"\n{element.content}\n")
            elif element.type == "figure":
                markdown_parts.append(f"![Figure]({element.content})\n")
            elif element.type == "caption":
                markdown_parts.append(f"*{element.content}*\n")
        
        return "\n".join(markdown_parts)
    
    def _calculate_stats(self, elements: List[ExtractedElement]) -> Dict[str, int]:
        """Calculate statistics from extracted elements"""
        stats = {
            "total_elements": len(elements),
            "titles": 0,
            "headers": 0,
            "paragraphs": 0,
            "tables": 0,
            "figures": 0,
            "lists": 0,
            "total_pages": max([e.page for e in elements]) if elements else 1
        }
        
        for element in elements:
            if element.type == "title":
                stats["titles"] += 1
            elif element.type == "header":
                stats["headers"] += 1
            elif element.type == "paragraph":
                stats["paragraphs"] += 1
            elif element.type == "table":
                stats["tables"] += 1
            elif element.type == "figure":
                stats["figures"] += 1
            elif element.type == "list":
                stats["lists"] += 1
        
        return stats
    
    def _fallback_extraction(self, pdf_bytes: bytes, filename: str, start_time: float) -> Dict[str, Any]:
        """Fallback extraction using PyPDF if Docling fails"""
        try:
            import pypdf
            
            logger.info("Using PyPDF fallback extraction")
            
            pdf_file = io.BytesIO(pdf_bytes)
            reader = pypdf.PdfReader(pdf_file)
            
            elements = []
            markdown_parts = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                
                if text.strip():
                    # Create a simple paragraph element
                    element = ExtractedElement(
                        type="paragraph",
                        content=text.strip(),
                        bbox=None,
                        page=page_num
                    )
                    elements.append(element)
                    markdown_parts.append(f"## Page {page_num}\n\n{text}\n")
            
            markdown = "\n".join(markdown_parts)
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "status": "success",
                "model": "pypdf_fallback",
                "filename": filename,
                "markdown": markdown,
                "elements": [e.to_dict() for e in elements],
                "statistics": {
                    "total_elements": len(elements),
                    "total_pages": len(reader.pages),
                    "paragraphs": len(elements)
                },
                "processing_time_ms": round(processing_time, 2),
                "metadata": {
                    "note": "Fallback extraction used (Docling unavailable)"
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {e}")
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "status": "error",
                "model": self.model_name,
                "filename": filename,
                "error": str(e),
                "processing_time_ms": round(processing_time, 2)
            }