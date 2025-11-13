"""
LoreGuard Document Parser Service

Document parsing service using unstructured.io for extracting content from various formats.
Supports PDF, DOCX, HTML, images, and other document types with metadata extraction.
"""

import logging
import tempfile
import os
from typing import Dict, Any, List, Optional, Union, BinaryIO
from pathlib import Path
import hashlib
import mimetypes

# Document processing libraries
UNSTRUCTURED_AVAILABLE = False
try:
    from unstructured.partition.auto import partition
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.html import partition_html
    from unstructured.partition.docx import partition_docx
    from unstructured.partition.pptx import partition_pptx
    from unstructured.partition.text import partition_text
    from unstructured.partition.email import partition_email
    from unstructured.partition.image import partition_image
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

# Excel support (optional)
try:
    from unstructured.partition.xlsx import partition_xlsx
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

# OCR libraries
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# PDF processing
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Language detection
try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

from app.core.config import settings
from app.schemas.document import DocumentFormat, DocumentMetadata, ExtractedContent


logger = logging.getLogger(__name__)


class DocumentParserService:
    """Service for parsing documents and extracting content."""
    
    def __init__(self):
        self.supported_formats = self._get_supported_formats()
        self.max_file_size = settings.MAX_FILE_SIZE
        self.processing_timeout = settings.PROCESSING_TIMEOUT
        
        # Initialize OCR if available
        if TESSERACT_AVAILABLE and settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    def _get_supported_formats(self) -> List[str]:
        """Get list of supported document formats."""
        base_formats = [
            "application/pdf",
            "text/html", "text/plain", "text/markdown",
            "application/json", "application/xml", "text/xml"
        ]
        
        if UNSTRUCTURED_AVAILABLE:
            base_formats.extend([
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # XLSX
                "application/msword",  # DOC
                "application/vnd.ms-powerpoint",  # PPT
                "application/vnd.ms-excel",  # XLS
                "application/rtf",
                "message/rfc822",  # Email
            ])
        
        if TESSERACT_AVAILABLE:
            base_formats.extend([
                "image/jpeg", "image/png", "image/tiff", "image/bmp"
            ])
        
        return base_formats
    
    async def parse_document(
        self, 
        file_content: bytes, 
        filename: str,
        mime_type: Optional[str] = None,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse a document and extract content and metadata.
        
        Args:
            file_content: Binary content of the document
            filename: Original filename
            mime_type: MIME type of the document
            processing_options: Additional processing options
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        
        # Validate file size
        if len(file_content) > self.max_file_size:
            raise ValueError(f"File size {len(file_content)} exceeds maximum {self.max_file_size}")
        
        # Detect MIME type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
        
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Validate supported format
        if mime_type not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {mime_type}")
        
        # Set default processing options
        options = processing_options or {}
        extract_metadata = options.get('extract_metadata', True)
        extract_text = options.get('extract_text', True)
        extract_images = options.get('extract_images', False)
        extract_tables = options.get('extract_tables', True)
        enable_ocr = options.get('enable_ocr', True)
        
        logger.info(f"Parsing document: {filename} ({mime_type}, {len(file_content)} bytes)")
        
        try:
            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Parse based on format
                if mime_type == "application/pdf":
                    result = await self._parse_pdf(temp_file_path, options)
                elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                    result = await self._parse_word_document(temp_file_path, options)
                elif mime_type in ["application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/vnd.ms-powerpoint"]:
                    result = await self._parse_presentation(temp_file_path, options)
                elif mime_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                    result = await self._parse_spreadsheet(temp_file_path, options)
                elif mime_type in ["text/html"]:
                    result = await self._parse_html(temp_file_path, options)
                elif mime_type in ["text/plain", "text/markdown"]:
                    result = await self._parse_text(temp_file_path, options)
                elif mime_type.startswith("image/"):
                    result = await self._parse_image(temp_file_path, options)
                else:
                    # Use auto-detection for other formats
                    result = await self._parse_auto(temp_file_path, options)
                
                # Add file metadata
                result['file_metadata'] = {
                    'filename': filename,
                    'mime_type': mime_type,
                    'file_size': len(file_content),
                    'content_hash': hashlib.sha256(file_content).hexdigest()
                }
                
                # Detect language if requested
                if options.get('detect_language', True) and result.get('text_content'):
                    result['detected_language'] = self._detect_language(result['text_content'])
                
                logger.info(f"Successfully parsed document: {filename}")
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Failed to parse document {filename}: {e}")
            raise
    
    async def _parse_pdf(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF document."""
        
        result = {
            'text_content': '',
            'metadata': {},
            'tables': [],
            'images': [],
            'page_count': 0
        }
        
        try:
            if UNSTRUCTURED_AVAILABLE:
                # Use unstructured.io for PDF parsing
                elements = partition_pdf(
                    filename=file_path,
                    extract_images_in_pdf=options.get('extract_images', False),
                    infer_table_structure=options.get('extract_tables', True),
                    ocr_languages=options.get('ocr_languages', ['eng']),
                    strategy="hi_res" if options.get('enable_ocr', True) else "fast"
                )
                
                # Extract text content
                text_parts = []
                tables = []
                
                for element in elements:
                    if hasattr(element, 'text'):
                        text_parts.append(element.text)
                    
                    # Extract tables (ElementMetadata uses attributes, not dict .get())
                    if hasattr(element, 'metadata') and hasattr(element.metadata, 'text_as_html'):
                        if element.metadata.text_as_html:
                            tables.append({
                                'html': element.metadata.text_as_html,
                                'text': element.text
                            })
                
                result['text_content'] = '\n'.join(text_parts)
                result['tables'] = tables
                
            elif PYMUPDF_AVAILABLE:
                # Fallback to PyMuPDF
                doc = fitz.open(file_path)
                text_parts = []
                
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text_parts.append(page.get_text())
                
                result['text_content'] = '\n'.join(text_parts)
                result['page_count'] = doc.page_count
                
                # Extract metadata
                metadata = doc.metadata
                result['metadata'] = {
                    'title': metadata.get('title'),
                    'author': metadata.get('author'),
                    'subject': metadata.get('subject'),
                    'creator': metadata.get('creator'),
                    'producer': metadata.get('producer'),
                    'creation_date': metadata.get('creationDate'),
                    'modification_date': metadata.get('modDate')
                }
                
                doc.close()
            
            else:
                raise RuntimeError("No PDF processing library available")
                
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            # Try OCR as fallback if enabled
            if options.get('enable_ocr', True) and TESSERACT_AVAILABLE:
                result = await self._parse_pdf_with_ocr(file_path, options)
            else:
                raise
        
        return result
    
    async def _parse_pdf_with_ocr(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF using OCR as fallback."""
        
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("OCR not available")
        
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(
                file_path,
                dpi=settings.OCR_DPI,
                fmt='PNG'
            )
            
            text_parts = []
            for i, image in enumerate(images):
                # Perform OCR on each page
                text = pytesseract.image_to_string(
                    image,
                    lang='+'.join(options.get('ocr_languages', ['eng'])),
                    config='--psm 1'
                )
                text_parts.append(text)
            
            return {
                'text_content': '\n'.join(text_parts),
                'metadata': {},
                'tables': [],
                'images': [],
                'page_count': len(images),
                'ocr_used': True
            }
            
        except Exception as e:
            logger.error(f"PDF OCR parsing failed: {e}")
            raise
    
    async def _parse_word_document(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Word document."""
        
        if not UNSTRUCTURED_AVAILABLE:
            raise RuntimeError("Unstructured library not available")
        
        try:
            elements = partition_docx(
                filename=file_path,
                infer_table_structure=options.get('extract_tables', True)
            )
            
            text_parts = []
            tables = []
            
            for element in elements:
                if hasattr(element, 'text'):
                    text_parts.append(element.text)
                
                    # Extract tables (ElementMetadata uses attributes, not dict .get())
                    if hasattr(element, 'metadata') and hasattr(element.metadata, 'text_as_html'):
                        if element.metadata.text_as_html:
                            tables.append({
                                'html': element.metadata.text_as_html,
                                'text': element.text
                            })
            
            return {
                'text_content': '\n'.join(text_parts),
                'metadata': {},
                'tables': tables,
                'images': []
            }
            
        except Exception as e:
            logger.error(f"Word document parsing failed: {e}")
            raise
    
    async def _parse_presentation(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PowerPoint presentation."""
        
        if not UNSTRUCTURED_AVAILABLE:
            raise RuntimeError("Unstructured library not available")
        
        try:
            elements = partition_pptx(filename=file_path)
            
            text_parts = []
            for element in elements:
                if hasattr(element, 'text'):
                    text_parts.append(element.text)
            
            return {
                'text_content': '\n'.join(text_parts),
                'metadata': {},
                'tables': [],
                'images': []
            }
            
        except Exception as e:
            logger.error(f"Presentation parsing failed: {e}")
            raise
    
    async def _parse_spreadsheet(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Excel spreadsheet."""
        
        if not UNSTRUCTURED_AVAILABLE:
            raise RuntimeError("Unstructured library not available")
        
        try:
            elements = partition_xlsx(filename=file_path)
            
            text_parts = []
            tables = []
            
            for element in elements:
                if hasattr(element, 'text'):
                    text_parts.append(element.text)
                
                # Spreadsheet content is essentially tabular
                if hasattr(element, 'metadata'):
                    tables.append({
                        'text': element.text,
                        'type': 'spreadsheet_cell'
                    })
            
            return {
                'text_content': '\n'.join(text_parts),
                'metadata': {},
                'tables': tables,
                'images': []
            }
            
        except Exception as e:
            logger.error(f"Spreadsheet parsing failed: {e}")
            raise
    
    async def _parse_html(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse HTML document."""
        
        if not UNSTRUCTURED_AVAILABLE:
            raise RuntimeError("Unstructured library not available")
        
        try:
            elements = partition_html(filename=file_path)
            
            text_parts = []
            links = []
            
            for element in elements:
                # Extract text content
                if hasattr(element, 'text') and element.text:
                    # Filter out None and empty strings
                    text = str(element.text).strip()
                    if text:
                        text_parts.append(text)
                # Also try to get text from element directly if it's a string-like object
                elif hasattr(element, '__str__'):
                    text = str(element).strip()
                    if text and len(text) > 10:  # Only include substantial text
                        text_parts.append(text)
                
                # Extract links if available (ElementMetadata doesn't support .get())
                if hasattr(element, 'metadata') and hasattr(element.metadata, 'link_urls'):
                    if element.metadata.link_urls:
                        links.extend(element.metadata.link_urls)
            
            # If no text extracted, try fallback parsing with BeautifulSoup
            text_content = '\n'.join(text_parts) if text_parts else ''
            
            if not text_content or len(text_content.strip()) < 50:
                # Fallback to BeautifulSoup for HTML parsing
                try:
                    from bs4 import BeautifulSoup
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        text_content = soup.get_text(separator='\n', strip=True)
                        logger.info(f"Used BeautifulSoup fallback for HTML parsing, extracted {len(text_content)} chars")
                except Exception as fallback_error:
                    logger.warning(f"BeautifulSoup fallback also failed: {fallback_error}")
            
            if not text_content or len(text_content.strip()) < 10:
                logger.warning(f"No substantial text content extracted from HTML file: {file_path}")
                # Return minimal content to avoid complete failure
                text_content = f"[HTML document from {file_path} - text extraction limited]"
            
            return {
                'text_content': text_content,
                'metadata': {},
                'tables': [],
                'images': [],
                'links': list(set(links))  # Remove duplicates
            }
            
        except Exception as e:
            logger.error(f"HTML parsing failed: {e}", exc_info=True)
            raise
    
    async def _parse_text(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse plain text document."""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return {
                'text_content': content,
                'metadata': {},
                'tables': [],
                'images': []
            }
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            raise
    
    async def _parse_image(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse image document using OCR."""
        
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("OCR not available for image processing")
        
        try:
            # Perform OCR on the image
            image = Image.open(file_path)
            text = pytesseract.image_to_string(
                image,
                lang='+'.join(options.get('ocr_languages', ['eng'])),
                config='--psm 1'
            )
            
            return {
                'text_content': text,
                'metadata': {
                    'image_size': image.size,
                    'image_mode': image.mode
                },
                'tables': [],
                'images': [],
                'ocr_used': True
            }
            
        except Exception as e:
            logger.error(f"Image parsing failed: {e}")
            raise
    
    async def _parse_auto(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document using auto-detection."""
        
        if not UNSTRUCTURED_AVAILABLE:
            raise RuntimeError("Unstructured library not available")
        
        try:
            elements = partition(filename=file_path)
            
            text_parts = []
            tables = []
            
            for element in elements:
                if hasattr(element, 'text'):
                    text_parts.append(element.text)
                
                    # Extract tables (ElementMetadata uses attributes, not dict .get())
                    if hasattr(element, 'metadata') and hasattr(element.metadata, 'text_as_html'):
                        if element.metadata.text_as_html:
                            tables.append({
                                'html': element.metadata.text_as_html,
                                'text': element.text
                            })
            
            return {
                'text_content': '\n'.join(text_parts),
                'metadata': {},
                'tables': tables,
                'images': []
            }
            
        except Exception as e:
            logger.error(f"Auto parsing failed: {e}")
            raise
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect the language of the text."""
        
        if not LANGDETECT_AVAILABLE or not text.strip():
            return None
        
        try:
            # Use first 1000 characters for language detection
            sample_text = text[:1000]
            detected = detect(sample_text)
            return detected
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get available parsing capabilities."""
        
        return {
            'unstructured_available': UNSTRUCTURED_AVAILABLE,
            'tesseract_available': TESSERACT_AVAILABLE,
            'pymupdf_available': PYMUPDF_AVAILABLE,
            'langdetect_available': LANGDETECT_AVAILABLE,
            'supported_formats': len(self.supported_formats)
        }

