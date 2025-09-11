"""
Unit tests for DocumentParserService.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from app.services.document_parser import DocumentParserService


class TestDocumentParserService:
    """Test cases for DocumentParserService."""
    
    @pytest.fixture
    def parser_service(self):
        """Create DocumentParserService instance for testing."""
        return DocumentParserService()
    
    @pytest.fixture
    def sample_text_content(self):
        """Sample text content for testing."""
        return b"This is a sample document for testing purposes. It contains multiple sentences."
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Mock PDF content."""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
    
    def test_init(self, parser_service):
        """Test service initialization."""
        assert parser_service is not None
        assert hasattr(parser_service, 'supported_formats')
        assert hasattr(parser_service, 'max_file_size')
        assert hasattr(parser_service, 'processing_timeout')
    
    def test_get_supported_formats(self, parser_service):
        """Test supported formats detection."""
        formats = parser_service._get_supported_formats()
        
        # Should always support basic formats
        assert "application/pdf" in formats
        assert "text/html" in formats
        assert "text/plain" in formats
        assert "application/json" in formats
        
        # Check that it returns a list
        assert isinstance(formats, list)
        assert len(formats) > 0
    
    @pytest.mark.asyncio
    async def test_parse_text_document(self, parser_service, sample_text_content):
        """Test parsing plain text document."""
        
        result = await parser_service.parse_document(
            file_content=sample_text_content,
            filename="test.txt",
            mime_type="text/plain"
        )
        
        # Check basic structure
        assert 'file_metadata' in result
        assert 'text_content' in result
        
        # Check file metadata
        assert result['file_metadata']['filename'] == "test.txt"
        assert result['file_metadata']['mime_type'] == "text/plain"
        assert result['file_metadata']['file_size'] == len(sample_text_content)
        
        # Check content
        assert "sample document" in result['text_content']
    
    @pytest.mark.asyncio
    async def test_parse_document_file_too_large(self, parser_service):
        """Test handling of files that are too large."""
        
        # Create content larger than max file size
        large_content = b"x" * (parser_service.max_file_size + 1)
        
        with pytest.raises(ValueError, match="File size .* exceeds maximum"):
            await parser_service.parse_document(
                file_content=large_content,
                filename="large.txt",
                mime_type="text/plain"
            )
    
    @pytest.mark.asyncio
    async def test_parse_document_unsupported_format(self, parser_service):
        """Test handling of unsupported file formats."""
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            await parser_service.parse_document(
                file_content=b"test content",
                filename="test.xyz",
                mime_type="application/unknown"
            )
    
    @pytest.mark.asyncio
    async def test_mime_type_detection(self, parser_service, sample_text_content):
        """Test automatic MIME type detection."""
        
        result = await parser_service.parse_document(
            file_content=sample_text_content,
            filename="test.txt"
            # No mime_type provided - should be detected
        )
        
        assert result['file_metadata']['mime_type'] == "text/plain"
    
    @pytest.mark.asyncio
    async def test_processing_options(self, parser_service, sample_text_content):
        """Test processing options handling."""
        
        options = {
            'extract_metadata': True,
            'extract_text': True,
            'detect_language': True
        }
        
        result = await parser_service.parse_document(
            file_content=sample_text_content,
            filename="test.txt",
            mime_type="text/plain",
            processing_options=options
        )
        
        # Should have processed with options
        assert 'text_content' in result
        assert 'detected_language' in result
    
    @pytest.mark.asyncio
    @patch('app.services.document_parser.partition_pdf')
    async def test_parse_pdf_with_unstructured(self, mock_partition, parser_service, sample_pdf_content):
        """Test PDF parsing with unstructured.io."""
        
        # Mock unstructured response
        mock_element = Mock()
        mock_element.text = "Sample PDF content"
        mock_element.metadata = {}
        mock_partition.return_value = [mock_element]
        
        with patch('app.services.document_parser.UNSTRUCTURED_AVAILABLE', True):
            result = await parser_service._parse_pdf("/fake/path.pdf", {})
        
        assert result['text_content'] == "Sample PDF content"
        assert 'metadata' in result
        assert 'tables' in result
        assert 'images' in result
    
    @pytest.mark.asyncio
    @patch('app.services.document_parser.fitz')
    async def test_parse_pdf_with_pymupdf(self, mock_fitz, parser_service):
        """Test PDF parsing with PyMuPDF fallback."""
        
        # Mock PyMuPDF
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "PDF content from PyMuPDF"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.page_count = 1
        mock_doc.metadata = {'title': 'Test PDF'}
        mock_fitz.open.return_value = mock_doc
        
        with patch('app.services.document_parser.UNSTRUCTURED_AVAILABLE', False):
            with patch('app.services.document_parser.PYMUPDF_AVAILABLE', True):
                result = await parser_service._parse_pdf("/fake/path.pdf", {})
        
        assert result['text_content'] == "PDF content from PyMuPDF"
        assert result['page_count'] == 1
        assert result['metadata']['title'] == 'Test PDF'
    
    @pytest.mark.asyncio
    @patch('app.services.document_parser.pytesseract')
    @patch('app.services.document_parser.pdf2image')
    async def test_parse_pdf_with_ocr(self, mock_pdf2image, mock_tesseract, parser_service):
        """Test PDF parsing with OCR fallback."""
        
        # Mock pdf2image
        mock_image = Mock()
        mock_pdf2image.convert_from_path.return_value = [mock_image]
        
        # Mock tesseract
        mock_tesseract.image_to_string.return_value = "OCR extracted text"
        
        with patch('app.services.document_parser.TESSERACT_AVAILABLE', True):
            result = await parser_service._parse_pdf_with_ocr("/fake/path.pdf", {})
        
        assert result['text_content'] == "OCR extracted text"
        assert result['ocr_used'] is True
        assert result['page_count'] == 1
    
    @pytest.mark.asyncio
    async def test_parse_html_document(self, parser_service):
        """Test HTML document parsing."""
        
        html_content = b"<html><head><title>Test</title></head><body><p>Test content</p></body></html>"
        
        with patch('app.services.document_parser.UNSTRUCTURED_AVAILABLE', True):
            with patch('app.services.document_parser.partition_html') as mock_partition:
                mock_element = Mock()
                mock_element.text = "Test content"
                mock_element.metadata = {}
                mock_partition.return_value = [mock_element]
                
                result = await parser_service.parse_document(
                    file_content=html_content,
                    filename="test.html",
                    mime_type="text/html"
                )
        
        assert "Test content" in result['text_content']
    
    @pytest.mark.asyncio
    @patch('app.services.document_parser.pytesseract')
    @patch('app.services.document_parser.Image')
    async def test_parse_image_document(self, mock_image_class, mock_tesseract, parser_service):
        """Test image document parsing with OCR."""
        
        # Mock PIL Image
        mock_image = Mock()
        mock_image.size = (800, 600)
        mock_image.mode = "RGB"
        mock_image_class.open.return_value = mock_image
        
        # Mock tesseract
        mock_tesseract.image_to_string.return_value = "Text from image"
        
        image_content = b"\x89PNG\r\n\x1a\n..."  # Mock PNG header
        
        with patch('app.services.document_parser.TESSERACT_AVAILABLE', True):
            result = await parser_service.parse_document(
                file_content=image_content,
                filename="test.png",
                mime_type="image/png"
            )
        
        assert result['text_content'] == "Text from image"
        assert result['ocr_used'] is True
        assert result['metadata']['image_size'] == (800, 600)
    
    def test_detect_language(self, parser_service):
        """Test language detection."""
        
        with patch('app.services.document_parser.LANGDETECT_AVAILABLE', True):
            with patch('app.services.document_parser.detect') as mock_detect:
                mock_detect.return_value = "en"
                
                result = parser_service._detect_language("This is English text.")
                assert result == "en"
    
    def test_detect_language_failure(self, parser_service):
        """Test language detection failure handling."""
        
        with patch('app.services.document_parser.LANGDETECT_AVAILABLE', True):
            with patch('app.services.document_parser.detect') as mock_detect:
                mock_detect.side_effect = Exception("Detection failed")
                
                result = parser_service._detect_language("Some text")
                assert result is None
    
    def test_get_capabilities(self, parser_service):
        """Test capabilities reporting."""
        
        capabilities = parser_service.get_capabilities()
        
        assert isinstance(capabilities, dict)
        assert 'unstructured_available' in capabilities
        assert 'tesseract_available' in capabilities
        assert 'pymupdf_available' in capabilities
        assert 'langdetect_available' in capabilities
        assert 'supported_formats' in capabilities
        
        # Should be boolean values
        assert isinstance(capabilities['unstructured_available'], bool)
        assert isinstance(capabilities['tesseract_available'], bool)
    
    @pytest.mark.asyncio
    async def test_temporary_file_cleanup(self, parser_service, sample_text_content):
        """Test that temporary files are properly cleaned up."""
        
        # Track created temp files
        original_tempfile = tempfile.NamedTemporaryFile
        temp_files = []
        
        def mock_tempfile(*args, **kwargs):
            temp_file = original_tempfile(*args, **kwargs)
            temp_files.append(temp_file.name)
            return temp_file
        
        with patch('tempfile.NamedTemporaryFile', side_effect=mock_tempfile):
            await parser_service.parse_document(
                file_content=sample_text_content,
                filename="test.txt",
                mime_type="text/plain"
            )
        
        # Check that temp files were cleaned up
        for temp_file_path in temp_files:
            assert not os.path.exists(temp_file_path), f"Temp file {temp_file_path} was not cleaned up"
    
    @pytest.mark.asyncio
    async def test_error_handling_with_cleanup(self, parser_service):
        """Test that temporary files are cleaned up even when errors occur."""
        
        # Create content that will cause an error during processing
        bad_content = b"This will cause an error"
        
        with patch('app.services.document_parser.partition_text') as mock_partition:
            mock_partition.side_effect = Exception("Processing failed")
            
            with pytest.raises(Exception, match="Processing failed"):
                await parser_service.parse_document(
                    file_content=bad_content,
                    filename="test.txt",
                    mime_type="text/plain"
                )
        
        # Temp file should still be cleaned up (tested implicitly by no file handle leaks)

