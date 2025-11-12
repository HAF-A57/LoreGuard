"""
LoreGuard Metadata Extraction Service

Service for extracting structured metadata from documents including titles, authors,
organizations, publication dates, topics, and geographic scope.
"""

import logging
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Set
import json

# NLP libraries
try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Date parsing
try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

# Geographic extraction
try:
    import pycountry
    PYCOUNTRY_AVAILABLE = True
except ImportError:
    PYCOUNTRY_AVAILABLE = False

from app.core.config import settings
from app.schemas.document import DocumentMetadata, LanguageCode


logger = logging.getLogger(__name__)


class MetadataExtractorService:
    """Service for extracting structured metadata from document content."""
    
    def __init__(self):
        self.nlp_model = None
        self.country_names = set()
        self.region_names = set()
        self.llm_service = None
        
        # Initialize NLP model if available
        if SPACY_AVAILABLE:
            try:
                # Try to load English model
                self.nlp_model = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy English model")
            except IOError:
                logger.warning("spaCy English model not available")
        
        # Initialize geographic data
        if PYCOUNTRY_AVAILABLE:
            self._initialize_geographic_data()
        
        # Initialize LLM metadata extraction service (lazy import to avoid circular dependencies)
        try:
            from app.services.llm_metadata_extraction import LLMMetadataExtractionService
            self.llm_service = LLMMetadataExtractionService()
            logger.info("LLM metadata extraction service initialized")
        except Exception as e:
            logger.warning(f"Could not initialize LLM metadata extraction service: {e}")
            self.llm_service = None
    
    def _initialize_geographic_data(self):
        """Initialize geographic reference data."""
        
        try:
            # Country names
            for country in pycountry.countries:
                self.country_names.add(country.name.lower())
                if hasattr(country, 'official_name'):
                    self.country_names.add(country.official_name.lower())
            
            # Add common region names
            self.region_names.update([
                'europe', 'asia', 'africa', 'north america', 'south america',
                'oceania', 'middle east', 'eastern europe', 'western europe',
                'central asia', 'southeast asia', 'east asia', 'south asia',
                'sub-saharan africa', 'north africa', 'latin america',
                'caribbean', 'pacific', 'atlantic', 'mediterranean',
                'baltic states', 'nordic countries', 'scandinavia',
                'balkans', 'caucasus', 'central america'
            ])
            
            logger.info(f"Initialized geographic data: {len(self.country_names)} countries, {len(self.region_names)} regions")
            
        except Exception as e:
            logger.warning(f"Failed to initialize geographic data: {e}")
    
    async def extract_metadata(
        self, 
        text_content: str, 
        file_metadata: Dict[str, Any],
        processing_options: Optional[Dict[str, Any]] = None
    ) -> DocumentMetadata:
        """
        Extract structured metadata from document content.
        Uses LLM-based extraction if available, falls back to regex-based extraction.
        
        Args:
            text_content: Full text content of the document
            file_metadata: File-level metadata (filename, size, etc.)
            processing_options: Additional processing options
            
        Returns:
            DocumentMetadata object with extracted metadata
        """
        
        options = processing_options or {}
        use_llm = options.get('use_llm_extraction', True)  # Default to True
        
        logger.info(f"Extracting metadata from document ({len(text_content)} characters)")
        
        # Initialize metadata structure
        metadata = {
            'title': None,
            'authors': [],
            'organization': None,
            'publication_date': None,
            'language': None,
            'page_count': None,
            'word_count': None,
            'file_format': None,
            'file_size': None,
            'mime_type': None,
            'topics': [],
            'subjects': [],
            'geographic_scope': [],
            'confidence_score': 0.0,
            'processing_quality': 'unknown'
        }
        
        try:
            # Basic text statistics (always extract)
            metadata.update(self._extract_text_statistics(text_content))
            
            # File metadata (always extract)
            metadata.update(self._extract_file_metadata(file_metadata))
            
            # Try LLM-based extraction first if enabled and available
            llm_metadata = None
            if use_llm and self.llm_service:
                try:
                    artifact_uri = file_metadata.get('uri') or file_metadata.get('filename', 'unknown')
                    llm_metadata = await self.llm_service.extract_metadata_llm(
                        text_content=text_content,
                        artifact_uri=artifact_uri,
                        processing_options=options
                    )
                    
                    if llm_metadata:
                        logger.info("Successfully extracted metadata using LLM")
                        # Map LLM response to our metadata structure
                        if llm_metadata.get('title'):
                            metadata['title'] = llm_metadata['title']
                        if llm_metadata.get('authors'):
                            metadata['authors'] = llm_metadata['authors']
                        if llm_metadata.get('organization'):
                            metadata['organization'] = llm_metadata['organization']
                        if llm_metadata.get('publication_date'):
                            # Parse date string to datetime
                            try:
                                from dateutil import parser as date_parser
                                metadata['publication_date'] = date_parser.parse(llm_metadata['publication_date'])
                            except Exception:
                                logger.warning(f"Could not parse publication_date: {llm_metadata['publication_date']}")
                        if llm_metadata.get('topics'):
                            metadata['topics'] = llm_metadata['topics']
                        if llm_metadata.get('geo_location'):
                            metadata['geographic_scope'] = [llm_metadata['geo_location']]
                        if llm_metadata.get('language'):
                            metadata['language'] = llm_metadata['language']
                        
                        # Set high confidence for LLM extraction
                        metadata['confidence_score'] = 0.9
                        metadata['processing_quality'] = 'excellent'
                except Exception as e:
                    logger.warning(f"LLM metadata extraction failed, falling back to regex: {e}")
                    llm_metadata = None
            
            # Fall back to regex-based extraction if LLM didn't provide results
            if not llm_metadata:
                logger.info("Using regex-based metadata extraction")
                
                # Title extraction
                if not metadata.get('title'):
                    title = self._extract_title(text_content, file_metadata.get('filename', ''))
                    if title:
                        metadata['title'] = title
                
                # Author extraction
                if not metadata.get('authors'):
                    authors = self._extract_authors(text_content)
                    if authors:
                        metadata['authors'] = authors
                
                # Organization extraction
                if not metadata.get('organization'):
                    organization = self._extract_organization(text_content)
                    if organization:
                        metadata['organization'] = organization
                
                # Date extraction
                if not metadata.get('publication_date'):
                    pub_date = self._extract_publication_date(text_content)
                    if pub_date:
                        metadata['publication_date'] = pub_date
                
                # Topic and keyword extraction
                if not metadata.get('topics'):
                    topics = self._extract_topics(text_content)
                    if topics:
                        metadata['topics'] = topics
                
                # Subject classification
                subjects = self._extract_subjects(text_content)
                if subjects:
                    metadata['subjects'] = subjects
                
                # Geographic scope
                if not metadata.get('geographic_scope'):
                    geographic_scope = self._extract_geographic_scope(text_content)
                    if geographic_scope:
                        metadata['geographic_scope'] = geographic_scope
            
            # Language detection (if not already done)
            if not metadata.get('language') and options.get('detect_language', True):
                metadata['language'] = self._detect_language_code(text_content)
            
            # Calculate confidence score (if not already set by LLM)
            if metadata['confidence_score'] == 0.0:
                metadata['confidence_score'] = self._calculate_confidence_score(metadata, text_content)
            
            # Assess processing quality (if not already set by LLM)
            if metadata['processing_quality'] == 'unknown':
                metadata['processing_quality'] = self._assess_processing_quality(metadata, text_content)
            
            logger.info(f"Metadata extraction completed with confidence {metadata['confidence_score']:.2f}")
            
            return DocumentMetadata(**metadata)
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}", exc_info=True)
            # Return basic metadata even if extraction fails
            return DocumentMetadata(
                word_count=len(text_content.split()) if text_content else 0,
                file_size=file_metadata.get('file_size'),
                mime_type=file_metadata.get('mime_type'),
                confidence_score=0.1,
                processing_quality='failed'
            )
    
    def _extract_text_statistics(self, text: str) -> Dict[str, Any]:
        """Extract basic text statistics."""
        
        if not text:
            return {'word_count': 0}
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        return {
            'word_count': len(words),
            'character_count': len(text),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()])
        }
    
    def _extract_file_metadata(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from file information."""
        
        result = {}
        
        if 'file_size' in file_metadata:
            result['file_size'] = file_metadata['file_size']
        
        if 'mime_type' in file_metadata:
            result['mime_type'] = file_metadata['mime_type']
            
            # Map MIME type to document format
            mime_to_format = {
                'application/pdf': 'pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                'application/msword': 'doc',
                'text/html': 'html',
                'text/plain': 'txt',
                'text/markdown': 'markdown'
            }
            
            if file_metadata['mime_type'] in mime_to_format:
                result['file_format'] = mime_to_format[file_metadata['mime_type']]
        
        return result
    
    def _extract_title(self, text: str, filename: str) -> Optional[str]:
        """Extract document title."""
        
        if not text:
            return None
        
        # Try multiple title extraction strategies
        title_candidates = []
        
        # Strategy 1: Look for title patterns in first few lines
        lines = text.split('\n')[:10]  # First 10 lines
        for line in lines:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                # Check if line looks like a title
                if (line.isupper() or 
                    line.istitle() or 
                    re.match(r'^[A-Z][^.!?]*$', line)):
                    title_candidates.append((line, 0.8))
        
        # Strategy 2: Look for HTML title tags
        html_title_match = re.search(r'<title[^>]*>([^<]+)</title>', text, re.IGNORECASE)
        if html_title_match:
            title_candidates.append((html_title_match.group(1).strip(), 0.9))
        
        # Strategy 3: Look for markdown headers
        md_title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if md_title_match:
            title_candidates.append((md_title_match.group(1).strip(), 0.85))
        
        # Strategy 4: Use filename as fallback
        if filename:
            clean_filename = re.sub(r'\.[^.]+$', '', filename)  # Remove extension
            clean_filename = re.sub(r'[_-]', ' ', clean_filename)  # Replace underscores/dashes
            if len(clean_filename) > 5:
                title_candidates.append((clean_filename, 0.3))
        
        # Select best title candidate
        if title_candidates:
            title_candidates.sort(key=lambda x: x[1], reverse=True)
            return title_candidates[0][0]
        
        return None
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract document authors."""
        
        if not text:
            return []
        
        authors = []
        
        # Common author patterns
        author_patterns = [
            r'(?:by|author|written by|authored by)[\s:]+([A-Z][a-z]+ [A-Z][a-z]+(?:,\s*[A-Z][a-z]+ [A-Z][a-z]+)*)',
            r'([A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)',  # John A. Smith
            r'([A-Z][a-z]+, [A-Z]\.[A-Z]\.)',      # Smith, J.A.
            r'(Dr\. [A-Z][a-z]+ [A-Z][a-z]+)',     # Dr. John Smith
            r'(Prof\. [A-Z][a-z]+ [A-Z][a-z]+)',   # Prof. John Smith
        ]
        
        # Look in first 1000 characters where authors are typically mentioned
        search_text = text[:1000]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    # Clean up author name
                    author = re.sub(r'\s+', ' ', match.strip())
                    if len(author) > 3 and len(author) < 50:
                        authors.append(author)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_authors = []
        for author in authors:
            if author.lower() not in seen:
                seen.add(author.lower())
                unique_authors.append(author)
        
        return unique_authors[:5]  # Limit to 5 authors
    
    def _extract_organization(self, text: str) -> Optional[str]:
        """Extract publishing organization."""
        
        if not text:
            return None
        
        # Common organization patterns
        org_patterns = [
            r'(?:published by|publisher|organization)[\s:]+([A-Z][^.!?\n]+)',
            r'([A-Z][a-z]+ (?:University|Institute|Center|Centre|Foundation|Corporation|Inc\.|LLC|Ltd\.))',
            r'(NATO|UN|EU|RAND|CSIS|Brookings|Carnegie|Heritage)',  # Known organizations
            r'([A-Z][a-z]+ (?:Department|Ministry|Agency|Bureau|Office))',
        ]
        
        # Search in first 2000 characters
        search_text = text[:2000]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    org = match.strip()
                    if len(org) > 5 and len(org) < 100:
                        return org
        
        return None
    
    def _extract_publication_date(self, text: str) -> Optional[datetime]:
        """Extract publication date."""
        
        if not text or not DATEUTIL_AVAILABLE:
            return None
        
        # Date patterns
        date_patterns = [
            r'(?:published|date|dated)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:published|date|dated)[\s:]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(?:published|date|dated)[\s:]+([A-Z][a-z]+ \d{1,2}, \d{4})',
            r'(?:published|date|dated)[\s:]+(\d{1,2} [A-Z][a-z]+ \d{4})',
            r'(\d{4})',  # Just year as fallback
        ]
        
        # Search in first 1000 characters
        search_text = text[:1000]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse the date
                    parsed_date = date_parser.parse(match, fuzzy=True)
                    
                    # Sanity check: date should be reasonable
                    if 1900 <= parsed_date.year <= datetime.now().year + 1:
                        return parsed_date
                        
                except Exception:
                    continue
        
        return None
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics and keywords."""
        
        if not text:
            return []
        
        topics = []
        
        # Military/defense-related keywords
        military_keywords = [
            'defense', 'defence', 'military', 'security', 'nato', 'alliance',
            'warfare', 'strategy', 'tactical', 'operational', 'strategic',
            'intelligence', 'surveillance', 'reconnaissance', 'cybersecurity',
            'terrorism', 'counterterrorism', 'peacekeeping', 'deterrence',
            'arms control', 'nuclear', 'conventional', 'asymmetric'
        ]
        
        # Geographic/political keywords
        political_keywords = [
            'policy', 'diplomacy', 'international', 'bilateral', 'multilateral',
            'treaty', 'agreement', 'cooperation', 'conflict', 'crisis',
            'sanctions', 'trade', 'economic', 'political', 'governance'
        ]
        
        # Technology keywords
        tech_keywords = [
            'technology', 'artificial intelligence', 'ai', 'machine learning',
            'cyber', 'digital', 'information', 'communications', 'satellite',
            'drone', 'autonomous', 'robotics', 'sensors'
        ]
        
        all_keywords = military_keywords + political_keywords + tech_keywords
        
        # Count keyword occurrences
        text_lower = text.lower()
        keyword_counts = {}
        
        for keyword in all_keywords:
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            if count > 0:
                keyword_counts[keyword] = count
        
        # Sort by frequency and take top keywords
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        topics = [keyword for keyword, count in sorted_keywords[:10]]
        
        # Use NLP for additional topic extraction if available
        if self.nlp_model and text:
            try:
                doc = self.nlp_model(text[:5000])  # Limit text for performance
                
                # Extract named entities that could be topics
                for ent in doc.ents:
                    if ent.label_ in ['ORG', 'GPE', 'EVENT', 'PRODUCT']:
                        topic = ent.text.lower().strip()
                        if len(topic) > 3 and topic not in topics:
                            topics.append(topic)
                
            except Exception as e:
                logger.warning(f"NLP topic extraction failed: {e}")
        
        return topics[:15]  # Limit to 15 topics
    
    def _extract_subjects(self, text: str) -> List[str]:
        """Extract subject classifications."""
        
        if not text:
            return []
        
        subjects = []
        text_lower = text.lower()
        
        # Subject classification based on content
        subject_patterns = {
            'military strategy': ['strategy', 'strategic', 'planning', 'doctrine'],
            'defense policy': ['policy', 'defense', 'military policy', 'national security'],
            'international relations': ['international', 'diplomacy', 'foreign policy', 'relations'],
            'cybersecurity': ['cyber', 'cybersecurity', 'information security', 'digital'],
            'intelligence': ['intelligence', 'surveillance', 'reconnaissance', 'espionage'],
            'terrorism': ['terrorism', 'counterterrorism', 'extremism', 'radicalization'],
            'arms control': ['arms control', 'disarmament', 'non-proliferation', 'treaty'],
            'peacekeeping': ['peacekeeping', 'peacebuilding', 'conflict resolution'],
            'regional security': ['regional', 'bilateral', 'alliance', 'partnership'],
            'technology': ['technology', 'innovation', 'research', 'development']
        }
        
        for subject, keywords in subject_patterns.items():
            score = sum(len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower)) 
                       for keyword in keywords)
            if score >= 2:  # Threshold for subject classification
                subjects.append(subject)
        
        return subjects
    
    def _extract_geographic_scope(self, text: str) -> List[str]:
        """Extract geographic scope and regions mentioned."""
        
        if not text:
            return []
        
        geographic_entities = []
        text_lower = text.lower()
        
        # Check for country names
        for country in self.country_names:
            if re.search(r'\b' + re.escape(country) + r'\b', text_lower):
                geographic_entities.append(country.title())
        
        # Check for region names
        for region in self.region_names:
            if re.search(r'\b' + re.escape(region) + r'\b', text_lower):
                geographic_entities.append(region.title())
        
        # Use NLP for additional geographic entity extraction
        if self.nlp_model:
            try:
                doc = self.nlp_model(text[:5000])  # Limit text for performance
                
                for ent in doc.ents:
                    if ent.label_ in ['GPE', 'LOC']:  # Geopolitical entities and locations
                        entity = ent.text.strip()
                        if len(entity) > 2 and entity not in geographic_entities:
                            geographic_entities.append(entity)
                            
            except Exception as e:
                logger.warning(f"NLP geographic extraction failed: {e}")
        
        # Remove duplicates and limit results
        unique_entities = list(dict.fromkeys(geographic_entities))  # Preserve order
        return unique_entities[:10]  # Limit to 10 geographic entities
    
    def _detect_language_code(self, text: str) -> Optional[str]:
        """Detect language and return language code."""
        
        if not text:
            return None
        
        try:
            from langdetect import detect
            detected = detect(text[:1000])  # Use first 1000 characters
            
            # Map to our supported language codes
            lang_mapping = {
                'en': 'en', 'fr': 'fr', 'de': 'de', 'es': 'es', 'ru': 'ru',
                'zh': 'zh', 'ar': 'ar', 'pt': 'pt', 'it': 'it', 'ja': 'ja',
                'ko': 'ko', 'nl': 'nl', 'sv': 'sv', 'no': 'no', 'da': 'da',
                'fi': 'fi', 'pl': 'pl', 'tr': 'tr', 'he': 'he', 'th': 'th'
            }
            
            return lang_mapping.get(detected, detected)
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None
    
    def _calculate_confidence_score(self, metadata: Dict[str, Any], text: str) -> float:
        """Calculate confidence score for metadata extraction."""
        
        score = 0.0
        max_score = 0.0
        
        # Title extraction confidence
        max_score += 0.2
        if metadata.get('title'):
            score += 0.2
        
        # Author extraction confidence
        max_score += 0.15
        if metadata.get('authors'):
            score += 0.15 * min(len(metadata['authors']) / 2, 1.0)
        
        # Organization extraction confidence
        max_score += 0.1
        if metadata.get('organization'):
            score += 0.1
        
        # Date extraction confidence
        max_score += 0.1
        if metadata.get('publication_date'):
            score += 0.1
        
        # Topic extraction confidence
        max_score += 0.15
        if metadata.get('topics'):
            score += 0.15 * min(len(metadata['topics']) / 5, 1.0)
        
        # Geographic scope confidence
        max_score += 0.1
        if metadata.get('geographic_scope'):
            score += 0.1 * min(len(metadata['geographic_scope']) / 3, 1.0)
        
        # Text quality confidence
        max_score += 0.2
        if text and len(text) > 100:
            # Base score for having substantial text
            text_score = 0.1
            
            # Bonus for well-structured text
            if len(text.split()) > 500:
                text_score += 0.05
            if re.search(r'[.!?]', text):  # Has sentence endings
                text_score += 0.05
            
            score += text_score
        
        # Normalize score
        if max_score > 0:
            return min(score / max_score, 1.0)
        else:
            return 0.0
    
    def _assess_processing_quality(self, metadata: Dict[str, Any], text: str) -> str:
        """Assess overall processing quality."""
        
        confidence = metadata.get('confidence_score', 0.0)
        
        if confidence >= 0.8:
            return 'excellent'
        elif confidence >= 0.6:
            return 'good'
        elif confidence >= 0.4:
            return 'fair'
        elif confidence >= 0.2:
            return 'poor'
        else:
            return 'failed'

