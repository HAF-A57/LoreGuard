## Multilingual Document Processing Research

### Executive Summary
For LoreGuard's global facts and perspectives harvesting requirements, we need robust multilingual document processing capabilities including language detection, OCR for non-Latin scripts, and translation for evaluation. This enables capture of diverse viewpoints and narratives from international sources. Based on research, **polyglot for detection + LibreTranslate for translation + Tesseract with language packs** emerges as the recommended on-premises solution.

### Technology Comparison

#### Language Detection

##### polyglot (Recommended)
**Strengths:**
- **High Accuracy**: 99%+ accuracy for documents >50 characters
- **165+ Languages**: Comprehensive language coverage
- **Fast**: ~1ms detection time for typical documents
- **Offline**: No internet connectivity required
- **Python Native**: Easy integration with existing Python services
- **Unicode Support**: Handles mixed-script documents

**Implementation:**
```python
from polyglot.detect import Detector
from polyglot.detect.base import UnknownLanguage

class LanguageDetectionService:
    def __init__(self):
        self.supported_languages = {
            'en': 'English', 'zh': 'Chinese', 'ru': 'Russian', 
            'ar': 'Arabic', 'es': 'Spanish', 'fr': 'French',
            'de': 'German', 'ja': 'Japanese', 'ko': 'Korean',
            'fa': 'Persian', 'ur': 'Urdu', 'hi': 'Hindi'
        }
    
    def detect_language(self, text: str) -> dict:
        """Detect document language with confidence scoring"""
        try:
            detector = Detector(text)
            
            # Get primary language and confidence
            primary_lang = detector.language
            confidence = primary_lang.confidence
            
            # Check for mixed languages
            mixed_languages = []
            if len(detector.languages) > 1:
                mixed_languages = [
                    {'code': lang.code, 'name': lang.name, 'confidence': lang.confidence}
                    for lang in detector.languages[:3]  # Top 3 detected languages
                ]
            
            return {
                'primary_language': {
                    'code': primary_lang.code,
                    'name': primary_lang.name,
                    'confidence': confidence
                },
                'mixed_languages': mixed_languages,
                'is_reliable': confidence > 0.8,
                'requires_translation': primary_lang.code not in ['en'],
                'supported': primary_lang.code in self.supported_languages
            }
            
        except UnknownLanguage:
            return {
                'primary_language': {'code': 'unknown', 'name': 'Unknown', 'confidence': 0.0},
                'mixed_languages': [],
                'is_reliable': False,
                'requires_translation': False,
                'supported': False
            }
```

##### Alternative: langdetect
**Strengths:**
- **Lightweight**: Minimal dependencies
- **Google-based**: Uses Google's language detection library
- **Fast**: Good performance for short texts

**Weaknesses:**
- **Limited**: Only 55 languages supported
- **Less Accurate**: Lower accuracy than polyglot for mixed content
- **No Confidence Scores**: Binary detection only

#### Translation Services

##### LibreTranslate (Recommended for On-Premises)
**Strengths:**
- **Open Source**: MIT license, no API costs
- **Self-Hosted**: Complete on-premises deployment
- **API Compatible**: OpenAI-style REST API
- **30+ Languages**: Covers major world languages
- **Privacy**: No data sent to external services
- **Docker Ready**: Easy containerized deployment

**Deployment:**
```yaml
# LibreTranslate on-premises deployment
version: '3.8'
services:
  libretranslate:
    image: libretranslate/libretranslate:latest
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - LT_LOAD_ONLY=en,zh,ru,ar,es,fr,de,ja,ko,fa  # Load specific models
      - LT_SUGGESTIONS=false  # Disable suggestions for privacy
      - LT_DISABLE_WEB_UI=true  # API only
      - LT_API_KEYS=true  # Enable API key authentication
    volumes:
      - ./models:/app/db  # Persistent model storage
    command: >
      --api-keys
      --require-api-key-origin
      --load-only en,zh,ru,ar,es,fr,de,ja,ko,fa
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

**Integration:**
```python
import requests
import asyncio
from typing import Dict, List

class TranslationService:
    def __init__(self, base_url="http://libretranslate:5000", api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    async def translate_text(self, text: str, source_lang: str, target_lang: str = "en") -> dict:
        """Translate text to target language"""
        
        # Skip if already in target language
        if source_lang == target_lang:
            return {
                'translated_text': text,
                'source_language': source_lang,
                'target_language': target_lang,
                'translation_confidence': 1.0
            }
        
        try:
            response = self.session.post(f"{self.base_url}/translate", json={
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "format": "text"
            })
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'translated_text': result['translatedText'],
                    'source_language': source_lang,
                    'target_language': target_lang,
                    'translation_confidence': 0.85  # LibreTranslate doesn't provide confidence
                }
            else:
                raise TranslationError(f"Translation failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Translation failed for {source_lang} -> {target_lang}: {e}")
            raise TranslationError(f"Translation service error: {e}")
    
    async def translate_document_metadata(self, metadata: dict, source_lang: str) -> dict:
        """Translate key document metadata fields"""
        
        translatable_fields = ['title', 'abstract', 'keywords', 'summary']
        translated_metadata = metadata.copy()
        
        for field in translatable_fields:
            if field in metadata and metadata[field]:
                try:
                    translation_result = await self.translate_text(
                        metadata[field], source_lang, "en"
                    )
                    translated_metadata[f"{field}_translated"] = translation_result['translated_text']
                    translated_metadata[f"{field}_original"] = metadata[field]
                except TranslationError as e:
                    logger.warning(f"Failed to translate {field}: {e}")
                    translated_metadata[f"{field}_translated"] = metadata[field]
        
        # Add translation metadata
        translated_metadata['translation_info'] = {
            'source_language': source_lang,
            'target_language': 'en',
            'translation_service': 'LibreTranslate',
            'translated_at': datetime.utcnow().isoformat()
        }
        
        return translated_metadata
```

#### Multilingual OCR Support

##### Tesseract with Language Packs
**Strengths:**
- **100+ Languages**: Comprehensive script and language support
- **Script Support**: Latin, Cyrillic, Arabic, Chinese, Japanese, Korean, Devanagari
- **Configurable**: Language-specific optimizations
- **Open Source**: No licensing costs
- **Active Development**: Regular updates and improvements

**Configuration:**
```python
import pytesseract
from PIL import Image
import cv2
import numpy as np

class MultilingualOCRService:
    def __init__(self):
        # Language mapping for Tesseract
        self.language_codes = {
            'en': 'eng', 'zh': 'chi_sim+chi_tra', 'ru': 'rus',
            'ar': 'ara', 'es': 'spa', 'fr': 'fra',
            'de': 'deu', 'ja': 'jpn', 'ko': 'kor',
            'fa': 'fas', 'ur': 'urd', 'hi': 'hin'
        }
        
        # OCR configuration per script type
        self.script_configs = {
            'latin': '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;: ',
            'arabic': '--psm 6 --oem 1',
            'chinese': '--psm 6 --oem 1 -c preserve_interword_spaces=1',
            'cyrillic': '--psm 6 --oem 1',
            'devanagari': '--psm 6 --oem 1'
        }
    
    def detect_script_type(self, image) -> str:
        """Detect script type from image for OCR optimization"""
        
        # Simple heuristic based on character patterns
        sample_text = pytesseract.image_to_string(image, config='--psm 13')
        
        if any(ord(char) > 0x4E00 and ord(char) < 0x9FFF for char in sample_text):
            return 'chinese'
        elif any(ord(char) > 0x0600 and ord(char) < 0x06FF for char in sample_text):
            return 'arabic'
        elif any(ord(char) > 0x0400 and ord(char) < 0x04FF for char in sample_text):
            return 'cyrillic'
        elif any(ord(char) > 0x0900 and ord(char) < 0x097F for char in sample_text):
            return 'devanagari'
        else:
            return 'latin'
    
    async def extract_text_multilingual(self, image_path: str, detected_language: str = None) -> dict:
        """Extract text with language-specific OCR optimization"""
        
        # Load and preprocess image
        image = cv2.imread(image_path)
        processed_image = self._preprocess_for_ocr(image)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(processed_image)
        
        # Detect script type for optimization
        script_type = self.detect_script_type(pil_image)
        
        # Select appropriate language and config
        if detected_language and detected_language in self.language_codes:
            lang_code = self.language_codes[detected_language]
        else:
            # Fallback to auto-detection
            lang_code = 'eng+chi_sim+ara+rus+spa+fra'  # Multi-language detection
        
        config = self.script_configs.get(script_type, '--psm 6')
        
        try:
            # Extract text with confidence scores
            text = pytesseract.image_to_string(
                pil_image, 
                lang=lang_code, 
                config=config
            )
            
            # Get confidence scores per word
            data = pytesseract.image_to_data(
                pil_image,
                lang=lang_code,
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'extracted_text': text,
                'language_detected': detected_language,
                'script_type': script_type,
                'ocr_confidence': avg_confidence / 100,  # Normalize to 0-1
                'word_count': len(text.split()),
                'processing_method': f"tesseract_{lang_code}"
            }
            
        except Exception as e:
            logger.error(f"OCR failed for language {detected_language}: {e}")
            raise OCRError(f"Multilingual OCR failed: {e}")
    
    def _preprocess_for_ocr(self, image) -> np.ndarray:
        """Preprocess image for better OCR results"""
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Binarization
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
```

### Multilingual Pipeline Integration

#### Document Processing Workflow
```python
class MultilingualDocumentProcessor:
    def __init__(self):
        self.language_detector = LanguageDetectionService()
        self.translator = TranslationService()
        self.ocr_service = MultilingualOCRService()
        
    async def process_multilingual_document(self, artifact: Artifact) -> ProcessedDocument:
        """Complete multilingual document processing pipeline"""
        
        # Step 1: Extract text (with OCR if needed)
        if artifact.requires_ocr():
            ocr_result = await self.ocr_service.extract_text_multilingual(
                artifact.file_path
            )
            raw_text = ocr_result['extracted_text']
            processing_metadata = {
                'ocr_confidence': ocr_result['ocr_confidence'],
                'script_type': ocr_result['script_type']
            }
        else:
            raw_text = artifact.extract_text()
            processing_metadata = {'extraction_method': 'direct'}
        
        # Step 2: Detect language
        language_info = self.language_detector.detect_language(raw_text)
        
        # Step 3: Translate if needed
        translated_text = raw_text
        translation_metadata = {}
        
        if language_info['requires_translation'] and language_info['is_reliable']:
            try:
                translation_result = await self.translator.translate_text(
                    raw_text, 
                    language_info['primary_language']['code'],
                    'en'
                )
                translated_text = translation_result['translated_text']
                translation_metadata = {
                    'translated': True,
                    'source_language': language_info['primary_language'],
                    'translation_confidence': translation_result['translation_confidence']
                }
            except TranslationError as e:
                logger.warning(f"Translation failed: {e}")
                translation_metadata = {'translation_failed': True, 'error': str(e)}
        
        # Step 4: Extract metadata in original and translated versions
        original_metadata = await self._extract_metadata(raw_text, language_info['primary_language']['code'])
        
        if translation_metadata.get('translated'):
            translated_metadata = await self._extract_metadata(translated_text, 'en')
        else:
            translated_metadata = original_metadata
        
        return ProcessedDocument(
            artifact_id=artifact.id,
            original_text=raw_text,
            translated_text=translated_text,
            language_info=language_info,
            original_metadata=original_metadata,
            translated_metadata=translated_metadata,
            processing_metadata={
                **processing_metadata,
                **translation_metadata
            }
        )
```

#### Multilingual Evaluation Strategy
```python
class MultilingualEvaluationService:
    def __init__(self, llm_service, translation_service):
        self.llm = llm_service
        self.translator = translation_service
        
    async def evaluate_multilingual_artifact(self, processed_doc: ProcessedDocument, 
                                           rubric: Rubric) -> EvaluationResult:
        """Evaluate document with multilingual considerations for diverse perspectives"""
        
        # Use translated text for evaluation if available
        evaluation_text = processed_doc.translated_text
        evaluation_metadata = processed_doc.translated_metadata
        
        # Adjust rubric for multilingual context
        adjusted_rubric = self._adjust_rubric_for_language(
            rubric, 
            processed_doc.language_info
        )
        
        # Standard evaluation on translated content
        base_evaluation = await self.llm.evaluate_artifact(
            evaluation_text, 
            evaluation_metadata, 
            adjusted_rubric
        )
        
        # Apply multilingual adjustments
        adjusted_evaluation = self._apply_multilingual_adjustments(
            base_evaluation,
            processed_doc
        )
        
        return adjusted_evaluation
    
    def _adjust_rubric_for_language(self, rubric: Rubric, language_info: dict) -> Rubric:
        """Adjust evaluation rubric based on source language"""
        
        adjusted_rubric = rubric.copy()
        
        # Adjust credibility scoring for non-English sources
        if language_info['primary_language']['code'] != 'en':
            # Slightly lower threshold for non-English authoritative sources
            # as translation may introduce minor quality degradation
            if 'credibility' in adjusted_rubric.categories:
                adjusted_rubric.categories['credibility'].weight *= 0.95
        
        # Adjust rigor scoring if translation confidence is low
        translation_confidence = language_info.get('translation_confidence', 1.0)
        if translation_confidence < 0.8:
            if 'rigor' in adjusted_rubric.categories:
                adjusted_rubric.categories['rigor'].weight *= 0.9
        
        return adjusted_rubric
    
    def _apply_multilingual_adjustments(self, evaluation: EvaluationResult, 
                                      processed_doc: ProcessedDocument) -> EvaluationResult:
        """Apply post-evaluation adjustments for multilingual content"""
        
        adjusted_evaluation = evaluation.copy()
        
        # Add language processing metadata
        adjusted_evaluation.processing_metadata = {
            **evaluation.processing_metadata,
            'source_language': processed_doc.language_info['primary_language'],
            'translation_applied': processed_doc.processing_metadata.get('translated', False),
            'multilingual_processing': True
        }
        
        # Adjust confidence based on translation quality
        if processed_doc.processing_metadata.get('translated'):
            translation_confidence = processed_doc.processing_metadata.get('translation_confidence', 0.8)
            # Reduce overall confidence based on translation quality
            adjusted_evaluation.confidence *= translation_confidence
        
        # Add language-specific concerns
        if processed_doc.language_info['primary_language']['confidence'] < 0.8:
            if not adjusted_evaluation.concerns:
                adjusted_evaluation.concerns = []
            adjusted_evaluation.concerns.append(
                f"Low language detection confidence: {processed_doc.language_info['primary_language']['confidence']:.2f}"
            )
        
        return adjusted_evaluation
```

### Performance Optimization

#### Caching and Batch Processing
```python
from functools import lru_cache
import hashlib

class OptimizedMultilingualProcessor:
    def __init__(self):
        self.translation_cache = {}  # Redis cache in production
        
    @lru_cache(maxsize=10000)
    def cached_language_detection(self, text_hash: str, text: str) -> dict:
        """Cache language detection results"""
        return self.language_detector.detect_language(text)
    
    async def batch_translate(self, texts: List[str], source_lang: str, 
                            target_lang: str = "en") -> List[dict]:
        """Batch translation for efficiency"""
        
        # Check cache first
        cached_results = []
        texts_to_translate = []
        
        for text in texts:
            cache_key = f"{source_lang}:{target_lang}:{hashlib.md5(text.encode()).hexdigest()}"
            
            if cache_key in self.translation_cache:
                cached_results.append(self.translation_cache[cache_key])
            else:
                texts_to_translate.append((text, cache_key))
        
        # Translate uncached texts in batch
        if texts_to_translate:
            batch_request = {
                "q": [item[0] for item in texts_to_translate],
                "source": source_lang,
                "target": target_lang,
                "format": "text"
            }
            
            response = await self.translator.session.post(
                f"{self.translator.base_url}/translate_batch",
                json=batch_request
            )
            
            if response.status_code == 200:
                batch_results = response.json()
                
                # Cache results
                for (original_text, cache_key), translated in zip(texts_to_translate, batch_results):
                    result = {
                        'translated_text': translated['translatedText'],
                        'source_language': source_lang,
                        'target_language': target_lang,
                        'translation_confidence': 0.85
                    }
                    self.translation_cache[cache_key] = result
                    cached_results.append(result)
        
        return cached_results
```

### Language-Specific Processing Rules

#### Script-Specific Handling
```python
class ScriptSpecificProcessor:
    def __init__(self):
        self.processors = {
            'arabic': self._process_arabic_text,
            'chinese': self._process_chinese_text,
            'japanese': self._process_japanese_text,
            'korean': self._process_korean_text,
            'devanagari': self._process_devanagari_text
        }
    
    def _process_arabic_text(self, text: str) -> dict:
        """Arabic-specific text processing"""
        
        # Handle right-to-left text
        # Remove diacritics for better matching
        # Normalize different Arabic letter forms
        
        import arabic_reshaper
        from bidi.algorithm import get_display
        
        # Reshape Arabic text for proper display
        reshaped_text = arabic_reshaper.reshape(text)
        display_text = get_display(reshaped_text)
        
        return {
            'processed_text': display_text,
            'original_text': text,
            'processing_notes': ['arabic_reshaping', 'bidi_display'],
            'script_direction': 'rtl'
        }
    
    def _process_chinese_text(self, text: str) -> dict:
        """Chinese-specific text processing"""
        
        # Detect traditional vs simplified
        # Word segmentation for Chinese text
        
        import jieba
        
        # Segment Chinese text
        segmented = ' '.join(jieba.cut(text))
        
        return {
            'processed_text': segmented,
            'original_text': text,
            'processing_notes': ['chinese_segmentation'],
            'script_direction': 'ltr'
        }
```

### Monitoring and Quality Assurance

#### Multilingual Processing Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics for multilingual processing
language_detection_attempts = Counter('loreguard_language_detection_total', 'Language detection attempts', ['detected_language', 'confidence_level'])
translation_requests = Counter('loreguard_translation_requests_total', 'Translation requests', ['source_lang', 'target_lang', 'status'])
ocr_multilingual_attempts = Counter('loreguard_ocr_multilingual_total', 'Multilingual OCR attempts', ['script_type', 'language', 'success'])

class MultilingualProcessingMonitor:
    def __init__(self):
        self.quality_thresholds = {
            'language_detection_confidence': 0.8,
            'translation_confidence': 0.7,
            'ocr_confidence': 0.6
        }
    
    def track_language_detection(self, language_info: dict):
        """Track language detection quality"""
        
        primary_lang = language_info['primary_language']
        confidence_level = 'high' if primary_lang['confidence'] > 0.8 else 'low'
        
        language_detection_attempts.labels(
            detected_language=primary_lang['code'],
            confidence_level=confidence_level
        ).inc()
    
    def track_translation_quality(self, translation_result: dict, success: bool):
        """Track translation success and quality"""
        
        translation_requests.labels(
            source_lang=translation_result['source_language'],
            target_lang=translation_result['target_language'],
            status='success' if success else 'failure'
        ).inc()
    
    def assess_processing_quality(self, processed_doc: ProcessedDocument) -> dict:
        """Assess overall multilingual processing quality"""
        
        quality_scores = {}
        
        # Language detection quality
        lang_confidence = processed_doc.language_info['primary_language']['confidence']
        quality_scores['language_detection'] = lang_confidence
        
        # Translation quality (if applicable)
        if processed_doc.processing_metadata.get('translated'):
            trans_confidence = processed_doc.processing_metadata.get('translation_confidence', 0.5)
            quality_scores['translation'] = trans_confidence
        
        # OCR quality (if applicable)
        if 'ocr_confidence' in processed_doc.processing_metadata:
            quality_scores['ocr'] = processed_doc.processing_metadata['ocr_confidence']
        
        # Overall quality score
        overall_quality = sum(quality_scores.values()) / len(quality_scores)
        
        return {
            'quality_scores': quality_scores,
            'overall_quality': overall_quality,
            'meets_threshold': overall_quality > 0.7,
            'requires_human_review': overall_quality < 0.6
        }
```

## Open-Source LLM Translation Models

### Meta NLLB (No Language Left Behind) - Recommended
**Strengths:**
- **200+ Languages**: Most comprehensive language coverage available
- **High Quality**: State-of-the-art translation quality for low-resource languages
- **Multiple Sizes**: 600M, 1.3B, 3.3B parameter variants for different resource constraints
- **Specialized**: Purpose-built for translation, not general chat
- **Research Backed**: Extensive evaluation and benchmarking by Meta AI

**Deployment:**
```python
# NLLB model deployment with Hugging Face Transformers
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class NLLBTranslationService:
    def __init__(self, model_size="1.3B"):
        model_name = f"facebook/nllb-200-{model_size}"
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,  # Use half precision for efficiency
            device_map="auto"  # Automatic GPU allocation
        )
        
        # Language code mapping
        self.language_codes = {
            'en': 'eng_Latn', 'zh': 'zho_Hans', 'ru': 'rus_Cyrl',
            'ar': 'arb_Arab', 'es': 'spa_Latn', 'fr': 'fra_Latn',
            'de': 'deu_Latn', 'ja': 'jpn_Jpan', 'ko': 'kor_Hang',
            'fa': 'pes_Arab', 'ur': 'urd_Arab', 'hi': 'hin_Deva'
        }
    
    async def translate_text(self, text: str, source_lang: str, target_lang: str = "en") -> dict:
        """Translate text using NLLB model"""
        
        # Convert language codes
        src_code = self.language_codes.get(source_lang, source_lang)
        tgt_code = self.language_codes.get(target_lang, target_lang)
        
        # Tokenize with special tokens for translation
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=512
        )
        
        # Force target language token
        forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(tgt_code)
        
        # Generate translation
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=4,
                early_stopping=True,
                do_sample=False  # Deterministic for consistency
            )
        
        # Decode result
        translated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Calculate approximate confidence (NLLB doesn't provide scores)
        confidence = self._estimate_translation_confidence(text, translated_text, source_lang, target_lang)
        
        return {
            'translated_text': translated_text,
            'source_language': source_lang,
            'target_language': target_lang,
            'translation_confidence': confidence,
            'model': 'NLLB-200',
            'model_size': '1.3B'
        }
    
    def _estimate_translation_confidence(self, source: str, target: str, 
                                       source_lang: str, target_lang: str) -> float:
        """Estimate translation confidence using heuristics"""
        
        # Simple heuristics for confidence estimation
        factors = []
        
        # Length ratio (should be reasonable)
        length_ratio = len(target) / len(source) if source else 0
        if 0.5 <= length_ratio <= 2.0:
            factors.append(0.8)
        else:
            factors.append(0.4)
        
        # Character diversity (good translations have varied characters)
        unique_chars_ratio = len(set(target)) / len(target) if target else 0
        factors.append(min(unique_chars_ratio * 2, 1.0))
        
        # Language-specific factors
        if source_lang in ['zh', 'ja', 'ko'] and target_lang == 'en':
            # Asian languages often have different structures
            factors.append(0.7)
        elif source_lang in ['ar', 'fa', 'ur'] and target_lang == 'en':
            # RTL languages
            factors.append(0.75)
        else:
            factors.append(0.85)
        
        return sum(factors) / len(factors)
```

### Tower LLM (Specialized Translation Model)
**Strengths:**
- **Translation Optimized**: Specifically trained for translation tasks
- **10 Languages**: English, German, French, Spanish, Chinese, Portuguese, Italian, Russian, Korean, Dutch
- **LLaMA2 Based**: Proven architecture with translation specialization
- **Competitive Performance**: Matches GPT-3.5/GPT-4 on translation benchmarks
- **Instruction Tuned**: Follows natural language instructions for translation

**Implementation:**
```python
# Tower model for specialized translation
from transformers import AutoTokenizer, AutoModelForCausalLM

class TowerTranslationService:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("Unbabel/TowerInstruct-7B-v0.1")
        self.model = AutoModelForCausalLM.from_pretrained(
            "Unbabel/TowerInstruct-7B-v0.1",
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    async def translate_with_context(self, text: str, source_lang: str, 
                                   target_lang: str, context: str = "") -> dict:
        """Translate with additional context for better accuracy"""
        
        # Construct instruction prompt
        if context:
            prompt = f"""Translate the following {source_lang} text to {target_lang}.
Context: {context}

Text to translate: {text}

Translation:"""
        else:
            prompt = f"""Translate the following {source_lang} text to {target_lang}:

{text}

Translation:"""
        
        # Tokenize and generate
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.1,  # Low temperature for consistent translation
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Extract translation from response
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        translation = full_response.split("Translation:")[-1].strip()
        
        return {
            'translated_text': translation,
            'source_language': source_lang,
            'target_language': target_lang,
            'translation_confidence': 0.9,  # Tower typically high quality
            'model': 'Tower-Instruct-7B',
            'context_used': bool(context)
        }
```

### Hybrid Translation Architecture

#### Multi-Model Translation Strategy
```python
class HybridTranslationService:
    def __init__(self):
        self.libretranslate = LibreTranslateService()
        self.nllb = NLLBTranslationService()
        self.tower = TowerTranslationService()
        
        # Model selection based on language pairs and quality requirements
        self.model_preferences = {
            # High-resource language pairs -> LibreTranslate (fastest)
            ('en', 'es'): 'libretranslate',
            ('en', 'fr'): 'libretranslate',
            ('en', 'de'): 'libretranslate',
            
            # Medium-resource pairs -> Tower (best quality for supported languages)
            ('en', 'zh'): 'tower',
            ('en', 'ru'): 'tower',
            ('en', 'ko'): 'tower',
            
            # Low-resource or unsupported -> NLLB (best coverage)
            'default': 'nllb'
        }
    
    async def translate_with_best_model(self, text: str, source_lang: str, 
                                      target_lang: str, context: str = "") -> dict:
        """Select best translation model based on language pair"""
        
        # Determine best model for this language pair
        lang_pair = (source_lang, target_lang)
        reverse_pair = (target_lang, source_lang)
        
        if lang_pair in self.model_preferences:
            preferred_model = self.model_preferences[lang_pair]
        elif reverse_pair in self.model_preferences:
            preferred_model = self.model_preferences[reverse_pair]
        else:
            preferred_model = self.model_preferences['default']
        
        # Route to appropriate service
        if preferred_model == 'libretranslate':
            return await self.libretranslate.translate_text(text, source_lang, target_lang)
        elif preferred_model == 'tower':
            return await self.tower.translate_with_context(text, source_lang, target_lang, context)
        else:  # nllb
            return await self.nllb.translate_text(text, source_lang, target_lang)
    
    async def ensemble_translation(self, text: str, source_lang: str, 
                                 target_lang: str) -> dict:
        """Use multiple models and select best result"""
        
        # Get translations from multiple models
        translation_tasks = []
        
        # Always try NLLB for coverage
        translation_tasks.append(
            asyncio.create_task(self.nllb.translate_text(text, source_lang, target_lang))
        )
        
        # Try Tower if languages are supported
        if source_lang in ['en', 'de', 'fr', 'es', 'zh', 'pt', 'it', 'ru', 'ko', 'nl']:
            translation_tasks.append(
                asyncio.create_task(self.tower.translate_with_context(text, source_lang, target_lang))
            )
        
        # Try LibreTranslate for common pairs
        if (source_lang, target_lang) in [('en', 'es'), ('en', 'fr'), ('en', 'de')]:
            translation_tasks.append(
                asyncio.create_task(self.libretranslate.translate_text(text, source_lang, target_lang))
            )
        
        # Wait for all translations
        try:
            results = await asyncio.gather(*translation_tasks, return_exceptions=True)
            valid_results = [r for r in results if not isinstance(r, Exception)]
            
            if not valid_results:
                raise TranslationError("All translation services failed")
            
            # Select best result based on confidence and length
            best_result = max(valid_results, key=lambda x: (
                x['translation_confidence'] * 0.7 + 
                (len(x['translated_text']) / len(text) if text else 0) * 0.3
            ))
            
            # Add ensemble metadata
            best_result['ensemble_used'] = True
            best_result['models_attempted'] = len(translation_tasks)
            best_result['models_succeeded'] = len(valid_results)
            
            return best_result
            
        except Exception as e:
            logger.error(f"Ensemble translation failed: {e}")
            raise TranslationError(f"All translation attempts failed: {e}")
```

### Local LLM Deployment with Ollama

#### Ollama Integration for Translation
```python
# Ollama integration for local LLM translation
import requests
import json

class OllamaTranslationService:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.available_models = self._get_available_models()
        
        # Recommended models for translation
        self.translation_models = [
            "codellama:13b-instruct",  # Good for structured translation
            "mistral:7b-instruct",     # General purpose with translation capability
            "llama2:13b-chat",         # Multilingual chat model
        ]
    
    def _get_available_models(self) -> list:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return [model['name'] for model in response.json()['models']]
        except Exception:
            return []
    
    async def translate_with_ollama(self, text: str, source_lang: str, 
                                  target_lang: str, model: str = "mistral:7b-instruct") -> dict:
        """Translate using local Ollama model"""
        
        # Construct translation prompt
        prompt = f"""You are a professional translator. Translate the following text from {source_lang} to {target_lang}.
Provide only the translation, no explanations or additional text.

Source text ({source_lang}):
{text}

Translation ({target_lang}):"""
        
        # Call Ollama API
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "stop": ["\n\n", "Source text", "Translation:"]
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result['response'].strip()
                
                return {
                    'translated_text': translated_text,
                    'source_language': source_lang,
                    'target_language': target_lang,
                    'translation_confidence': 0.8,  # Estimated for LLM translation
                    'model': model,
                    'service': 'ollama'
                }
            else:
                raise TranslationError(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama translation failed: {e}")
            raise TranslationError(f"Local LLM translation failed: {e}")

# Ollama model deployment script
async def setup_ollama_translation_models():
    """Download and setup translation models in Ollama"""
    
    models_to_install = [
        "mistral:7b-instruct",     # Primary translation model
        "llama2:13b-chat",         # Backup model
        "codellama:13b-instruct"   # For technical documents
    ]
    
    for model in models_to_install:
        print(f"Installing {model}...")
        
        # Pull model
        response = requests.post(f"http://localhost:11434/api/pull", 
                               json={"name": model})
        
        if response.status_code == 200:
            print(f"✓ {model} installed successfully")
        else:
            print(f"✗ Failed to install {model}: {response.status_code}")
```

### Translation Quality Assessment

#### Quality Scoring and Validation
```python
class TranslationQualityAssessor:
    def __init__(self):
        self.quality_metrics = [
            'fluency',      # How natural the translation reads
            'accuracy',     # How well meaning is preserved
            'completeness', # All content translated
            'consistency'   # Consistent terminology
        ]
    
    async def assess_translation_quality(self, source_text: str, translated_text: str,
                                       source_lang: str, target_lang: str) -> dict:
        """Assess translation quality using multiple metrics"""
        
        quality_scores = {}
        
        # Length ratio check
        length_ratio = len(translated_text) / len(source_text) if source_text else 0
        quality_scores['length_ratio'] = self._score_length_ratio(length_ratio, source_lang, target_lang)
        
        # Character diversity
        char_diversity = len(set(translated_text)) / len(translated_text) if translated_text else 0
        quality_scores['character_diversity'] = min(char_diversity * 2, 1.0)
        
        # Detect obvious translation artifacts
        artifacts_score = self._detect_translation_artifacts(translated_text)
        quality_scores['artifacts'] = artifacts_score
        
        # Overall quality score
        overall_quality = sum(quality_scores.values()) / len(quality_scores)
        
        return {
            'quality_scores': quality_scores,
            'overall_quality': overall_quality,
            'quality_grade': self._grade_quality(overall_quality),
            'requires_human_review': overall_quality < 0.6
        }
    
    def _score_length_ratio(self, ratio: float, source_lang: str, target_lang: str) -> float:
        """Score translation based on length ratio expectations"""
        
        # Expected ratios for different language pairs
        expected_ratios = {
            ('zh', 'en'): (0.8, 1.5),  # Chinese to English
            ('ar', 'en'): (0.7, 1.3),  # Arabic to English
            ('de', 'en'): (0.8, 1.2),  # German to English
            ('default'): (0.6, 1.8)    # General range
        }
        
        lang_pair = (source_lang, target_lang)
        expected_range = expected_ratios.get(lang_pair, expected_ratios['default'])
        
        if expected_range[0] <= ratio <= expected_range[1]:
            return 1.0
        elif ratio < expected_range[0]:
            return max(0.3, ratio / expected_range[0])
        else:
            return max(0.3, expected_range[1] / ratio)
    
    def _detect_translation_artifacts(self, text: str) -> float:
        """Detect common translation artifacts that indicate poor quality"""
        
        artifacts = [
            'TRANSLATE:', 'TRANSLATION:', '[UNTRANSLATABLE]',
            '***', '###', 'ERROR:', 'FAILED:',
            'I cannot translate', 'Unable to translate'
        ]
        
        artifact_count = sum(1 for artifact in artifacts if artifact.lower() in text.lower())
        
        # Score inversely proportional to artifact count
        return max(0.0, 1.0 - (artifact_count * 0.3))
```

### Deployment Configuration

#### Docker Compose with All Translation Services
```yaml
version: '3.8'
services:
  # LibreTranslate for fast, basic translation
  libretranslate:
    image: libretranslate/libretranslate:latest
    ports:
      - "5000:5000"
    environment:
      - LT_LOAD_ONLY=en,zh,ru,ar,es,fr,de,ja,ko,fa
      - LT_API_KEYS=true
    volumes:
      - ./libretranslate-models:/app/db
    deploy:
      resources:
        limits:
          memory: 4G

  # Ollama for LLM-based translation
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./ollama-models:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # NLLB model server (custom container)
  nllb-server:
    build: ./nllb-server
    ports:
      - "5001:5001"
    environment:
      - MODEL_SIZE=1.3B
      - TORCH_DEVICE=cuda
    volumes:
      - ./nllb-models:/app/models
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Translation coordinator
  translation-coordinator:
    build: ./translation-coordinator
    ports:
      - "8080:8080"
    environment:
      - LIBRETRANSLATE_URL=http://libretranslate:5000
      - OLLAMA_URL=http://ollama:11434
      - NLLB_URL=http://nllb-server:5001
    depends_on:
      - libretranslate
      - ollama
      - nllb-server
```

### Performance and Cost Analysis

#### Translation Speed Comparison
- **LibreTranslate**: 100-500 words/second (CPU)
- **NLLB**: 50-200 words/second (GPU recommended)
- **Tower**: 30-150 words/second (GPU recommended)
- **Ollama**: 20-100 words/second (depends on model size)

#### Resource Requirements
- **LibreTranslate**: 2-4GB RAM, CPU-only
- **NLLB-1.3B**: 4-8GB RAM, 4-8GB VRAM
- **Tower-7B**: 8-16GB RAM, 8-16GB VRAM
- **Ollama**: Variable (4-32GB depending on model)

#### Cost Analysis (Annual, On-Premises)
- **Hardware**: $20K (GPU servers for LLM models)
- **Power**: $5K (additional GPU power consumption)
- **Storage**: $2K (model storage)
- **Total**: $27K additional for LLM translation capability

### Next Steps
1. **Deploy LibreTranslate** with language model configuration
2. **Configure Tesseract** with multilingual language packs
3. **Implement language detection** pipeline with polyglot
4. **Build translation caching** system for efficiency
5. **Create quality monitoring** for multilingual processing
6. **Deploy NLLB model** for comprehensive language coverage
7. **Set up Ollama** with translation-optimized models
8. **Implement ensemble translation** for critical documents

### Open Questions Resolved
- [x] **Language Detection**: polyglot for comprehensive coverage
- [x] **Traditional Translation**: LibreTranslate for on-premises deployment
- [x] **LLM Translation**: NLLB + Tower + Ollama hybrid approach
- [x] **Multilingual OCR**: Tesseract with language-specific configurations
- [x] **Evaluation Strategy**: Translate-then-evaluate with confidence adjustments
- [x] **Quality Assurance**: Confidence scoring with human review thresholds
- [x] **Model Selection**: Tiered approach based on language pair and quality requirements
