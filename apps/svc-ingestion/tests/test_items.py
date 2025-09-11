"""
Unit tests for LoreGuard Ingestion Service items.
"""

import pytest
from datetime import datetime

from app.items import (
    ArtifactItem, DocumentMetadataItem, SourceConfigItem,
    ArtifactItemLoader, DocumentMetadataItemLoader
)


class TestArtifactItem:
    """Test ArtifactItem functionality."""
    
    def test_artifact_item_creation(self):
        """Test basic artifact item creation."""
        item = ArtifactItem()
        
        # Test setting basic fields
        item['uri'] = 'https://example.com/document.html'
        item['source_id'] = 'test-source'
        item['content_hash'] = 'abc123'
        item['text_content'] = 'This is test content.'
        
        assert item['uri'] == 'https://example.com/document.html'
        assert item['source_id'] == 'test-source'
        assert item['content_hash'] == 'abc123'
        assert item['text_content'] == 'This is test content.'
    
    def test_artifact_item_required_fields(self):
        """Test that artifact item handles missing fields gracefully."""
        item = ArtifactItem()
        
        # Should not raise error for missing fields
        assert item.get('uri') is None
        assert item.get('nonexistent_field') is None
    
    def test_artifact_item_with_binary_content(self):
        """Test artifact item with binary content."""
        item = ArtifactItem()
        
        binary_content = b'This is binary content'
        item['raw_content'] = binary_content
        item['content_length'] = len(binary_content)
        
        assert item['raw_content'] == binary_content
        assert item['content_length'] == len(binary_content)


class TestDocumentMetadataItem:
    """Test DocumentMetadataItem functionality."""
    
    def test_metadata_item_creation(self):
        """Test basic metadata item creation."""
        item = DocumentMetadataItem()
        
        item['artifact_uri'] = 'https://example.com/document.html'
        item['title'] = 'Test Document'
        item['authors'] = ['John Doe', 'Jane Smith']
        item['organization'] = 'Test Organization'
        item['topics'] = ['security', 'defense']
        
        assert item['artifact_uri'] == 'https://example.com/document.html'
        assert item['title'] == 'Test Document'
        assert item['authors'] == ['John Doe', 'Jane Smith']
        assert item['organization'] == 'Test Organization'
        assert item['topics'] == ['security', 'defense']
    
    def test_metadata_item_date_handling(self):
        """Test metadata item with publication date."""
        item = DocumentMetadataItem()
        
        # Test with ISO date string
        item['publication_date'] = '2024-01-15T10:30:00'
        assert item['publication_date'] == '2024-01-15T10:30:00'


class TestSourceConfigItem:
    """Test SourceConfigItem functionality."""
    
    def test_source_config_creation(self):
        """Test basic source config creation."""
        item = SourceConfigItem()
        
        item['source_id'] = 'test-source-123'
        item['name'] = 'Test News Source'
        item['base_url'] = 'https://testnews.com'
        item['source_type'] = 'news'
        item['status'] = 'active'
        
        assert item['source_id'] == 'test-source-123'
        assert item['name'] == 'Test News Source'
        assert item['base_url'] == 'https://testnews.com'
        assert item['source_type'] == 'news'
        assert item['status'] == 'active'
    
    def test_source_config_with_arrays(self):
        """Test source config with array fields."""
        item = SourceConfigItem()
        
        item['allowed_domains'] = ['testnews.com', 'www.testnews.com']
        item['start_urls'] = ['https://testnews.com/news', 'https://testnews.com/articles']
        item['include_patterns'] = [r'/news/\d+/', r'/article/.*']
        
        assert len(item['allowed_domains']) == 2
        assert len(item['start_urls']) == 2
        assert len(item['include_patterns']) == 2


class TestItemLoaders:
    """Test item loaders functionality."""
    
    def test_artifact_item_loader(self):
        """Test ArtifactItemLoader processing."""
        loader = ArtifactItemLoader()
        
        # Test text cleaning
        loader.add_value('uri', '  https://example.com/test  ')
        loader.add_value('text_content', '  This is   test content   with   extra   spaces  ')
        
        item = loader.load_item()
        
        assert item['uri'] == 'https://example.com/test'
        # Text content should be cleaned of extra whitespace
        assert 'extra   spaces' not in item['text_content']
    
    def test_document_metadata_loader(self):
        """Test DocumentMetadataItemLoader processing."""
        loader = DocumentMetadataItemLoader()
        
        # Test author processing
        loader.add_value('authors', 'John Doe, Jane Smith; Bob Wilson')
        loader.add_value('topics', 'security, defense; military, strategy')
        
        item = loader.load_item()
        
        # Should split authors and topics on commas and semicolons
        assert 'John Doe' in item['authors']
        assert 'Jane Smith' in item['authors']
        assert 'Bob Wilson' in item['authors']
        
        assert 'security' in item['topics']
        assert 'defense' in item['topics']
        assert 'military' in item['topics']
        assert 'strategy' in item['topics']


class TestItemValidation:
    """Test item validation and error handling."""
    
    def test_artifact_item_validation(self):
        """Test artifact item validation."""
        item = ArtifactItem()
        
        # Test with valid data
        item['uri'] = 'https://example.com/valid'
        item['content_hash'] = 'valid_hash_123'
        item['text_content'] = 'Valid content with sufficient length for processing'
        
        # Should not raise any errors
        assert item['uri'] == 'https://example.com/valid'
    
    def test_metadata_item_validation(self):
        """Test metadata item validation."""
        item = DocumentMetadataItem()
        
        # Test with minimal valid data
        item['artifact_uri'] = 'https://example.com/document'
        item['title'] = 'Valid Document Title'
        
        assert item['artifact_uri'] == 'https://example.com/document'
        assert item['title'] == 'Valid Document Title'


if __name__ == '__main__':
    pytest.main([__file__])

