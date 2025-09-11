## Document Conversion and OCR Research Findings

### Executive Summary
For LoreGuard's document normalization service, we need a solution that can handle diverse document formats (PDF, DOCX, HTML, images) with high accuracy and reasonable cost. Based on research, **unstructured.io with Tesseract fallback** emerges as the recommended approach for open-source deployment, with AWS Textract as a premium option for critical documents.

### Technology Comparison

#### unstructured.io
**Strengths:**
- Open-source Python library designed for ML preprocessing pipelines
- Supports 20+ document formats (PDF, DOCX, PPTX, HTML, XML, images)
- Built-in partitioning (headers, paragraphs, tables, lists)
- Excellent for extracting structured data from unstructured documents
- Active development and community support
- Can be deployed on-premises for security compliance
- Integrates well with modern ML/AI workflows

**Weaknesses:**
- Newer library with smaller community than established tools
- OCR accuracy depends on underlying engines (Tesseract by default)
- May require fine-tuning for specific document types

**Use Case:** Primary document processing engine for most document types

#### GROBID (GeneRation Of BIbliographic Data)
**Strengths:**
- Specifically designed for scientific/academic document processing
- Excellent at extracting bibliographic information and citations
- Strong performance on research papers, technical reports
- Open-source with mature codebase
- Good at handling complex document structures
- Supports PDF to structured XML conversion

**Weaknesses:**
- Limited to academic/scientific documents
- Java-based (deployment complexity)
- Requires significant computational resources
- Not suitable for general document processing

**Use Case:** Specialized processor for academic papers and technical reports

#### Tesseract OCR
**Strengths:**
- Industry-standard open-source OCR engine
- Supports 100+ languages
- Highly configurable and customizable
- No licensing costs
- Can be fine-tuned for specific document types
- Excellent community support and documentation

**Weaknesses:**
- Requires significant preprocessing for good results
- Lower accuracy on complex layouts compared to commercial solutions
- Struggles with handwritten text and poor-quality scans
- No built-in document structure understanding

**Use Case:** Fallback OCR engine for image-based documents and scanned PDFs

#### AWS Textract
**Strengths:**
- State-of-the-art accuracy for text and table extraction
- Excellent handling of forms and complex layouts
- Built-in document structure analysis
- Scalable cloud service with high availability
- Supports handwriting recognition
- No infrastructure management required

**Weaknesses:**
- Proprietary service with usage costs
- Requires internet connectivity
- Data sovereignty concerns for classified documents
- Limited customization options
- Vendor lock-in risk

**Use Case:** Premium option for high-value or complex documents

### Recommended Architecture: Tiered Processing

#### Tier 1: unstructured.io (Primary)
```python
from unstructured.partition.auto import partition

# Primary document processing
def process_document_primary(file_path):
    elements = partition(filename=file_path)
    
    # Extract structured content
    content = {
        'text': '\n'.join([str(el) for el in elements]),
        'tables': [el for el in elements if el.category == 'Table'],
        'headers': [el for el in elements if el.category == 'Title'],
        'metadata': extract_metadata(elements)
    }
    return content
```

#### Tier 2: GROBID (Academic Documents)
```python
# For academic/scientific documents
def process_academic_document(file_path):
    if is_academic_document(file_path):
        # Use GROBID for enhanced academic processing
        return grobid_client.process_fulltext_document(file_path)
    return None
```

#### Tier 3: Tesseract (OCR Fallback)
```python
import pytesseract
from PIL import Image

# Fallback OCR for image-heavy documents
def process_with_ocr(file_path):
    if requires_ocr(file_path):
        # Convert PDF pages to images if needed
        images = convert_pdf_to_images(file_path)
        
        text = ""
        for image in images:
            # Apply preprocessing for better OCR
            processed_image = preprocess_for_ocr(image)
            text += pytesseract.image_to_string(processed_image)
        
        return {'text': text, 'source': 'ocr'}
    return None
```

#### Tier 4: AWS Textract (Premium)
```python
import boto3

# Premium processing for high-value documents
def process_with_textract(file_path, confidence_threshold=0.9):
    textract = boto3.client('textract')
    
    # For documents requiring highest accuracy
    if is_high_value_document(file_path):
        response = textract.analyze_document(
            Document={'Bytes': open(file_path, 'rb').read()},
            FeatureTypes=['TABLES', 'FORMS']
        )
        return parse_textract_response(response)
    return None
```

### Processing Pipeline Integration

#### Document Type Detection
```python
def classify_document_type(file_path):
    """Determine optimal processing strategy"""
    mime_type = get_mime_type(file_path)
    
    if is_academic_paper(file_path):
        return 'academic'
    elif mime_type in ['image/jpeg', 'image/png'] or is_scanned_pdf(file_path):
        return 'ocr_required'
    elif is_high_value_document(file_path):
        return 'premium'
    else:
        return 'standard'
```

#### Cascading Processing Logic
```python
async def process_document(file_path, quality_threshold=0.8):
    """Process document with fallback strategy"""
    
    doc_type = classify_document_type(file_path)
    
    # Try primary processor
    result = await process_document_primary(file_path)
    
    if result.quality_score < quality_threshold:
        # Try specialized processors based on type
        if doc_type == 'academic':
            fallback_result = await process_academic_document(file_path)
        elif doc_type == 'ocr_required':
            fallback_result = await process_with_ocr(file_path)
        elif doc_type == 'premium':
            fallback_result = await process_with_textract(file_path)
        
        # Use better result
        if fallback_result and fallback_result.quality_score > result.quality_score:
            result = fallback_result
    
    return result
```

### Performance and Cost Analysis

#### Processing Speed (pages/minute)
- **unstructured.io**: 10-50 pages/minute
- **GROBID**: 5-15 pages/minute  
- **Tesseract**: 1-5 pages/minute
- **AWS Textract**: 20-100 pages/minute (network dependent)

#### Accuracy Estimates
- **unstructured.io**: 85-95% (format dependent)
- **GROBID**: 90-98% (academic documents)
- **Tesseract**: 70-90% (quality dependent)
- **AWS Textract**: 95-99% (most document types)

#### Cost Analysis (per 1000 pages) - ON-PREMISES FOCUS
- **unstructured.io**: $0 (compute costs only, open-source)
- **GROBID**: $0 (compute costs only, open-source)
- **Tesseract**: $0 (compute costs only, open-source)
- **AWS Textract**: NOT AVAILABLE (cloud-only, incompatible with on-premises requirement)

### Deployment Strategy

#### Infrastructure Requirements (ON-PREMISES ONLY)
```yaml
# Docker deployment - fully on-premises
services:
  document-processor:
    image: loreguard/document-processor
    environment:
      - UNSTRUCTURED_API_KEY=${UNSTRUCTURED_API_KEY}  # Optional for enhanced features
      - ENABLE_GROBID=true
      - ENABLE_TEXTRACT=false  # Cloud service - disabled for on-premises
      - STORAGE_BACKEND=minio  # Local MinIO instead of S3
      - MINIO_ENDPOINT=http://minio:9000
    volumes:
      - ./documents:/app/documents
      - ./models:/app/models
      - ./local-storage:/app/storage  # Local persistent storage
    resources:
      cpu: 2-4 cores
      memory: 4-8GB
```

#### Processing Queue Integration
```python
# Celery task for async processing
@celery.task(bind=True, max_retries=3)
def process_document_task(self, artifact_id, file_path, processing_tier='standard'):
    try:
        result = process_document(file_path, tier=processing_tier)
        
        # Store processed content
        store_normalized_content(artifact_id, result)
        
        # Emit processing complete event
        emit_event('document.normalized', {
            'artifact_id': artifact_id,
            'processing_tier': processing_tier,
            'quality_score': result.quality_score
        })
        
        return result
        
    except Exception as exc:
        # Retry with lower tier on failure
        if processing_tier == 'premium':
            return self.retry(args=[artifact_id, file_path, 'standard'], countdown=60)
        raise exc
```

### Quality Assurance

#### Confidence Scoring
```python
def calculate_quality_score(processed_content):
    """Calculate confidence score for processed content"""
    
    factors = {
        'text_length': min(len(processed_content.text) / 1000, 1.0),
        'structure_detected': 1.0 if processed_content.has_structure else 0.5,
        'metadata_extracted': 1.0 if processed_content.metadata else 0.7,
        'ocr_confidence': getattr(processed_content, 'ocr_confidence', 1.0)
    }
    
    # Weighted average
    weights = {'text_length': 0.3, 'structure_detected': 0.3, 
               'metadata_extracted': 0.2, 'ocr_confidence': 0.2}
    
    score = sum(factors[k] * weights[k] for k in factors)
    return min(score, 1.0)
```

#### Human Review Queue
```python
def requires_human_review(processed_content):
    """Determine if document needs human review"""
    
    return (
        processed_content.quality_score < 0.7 or
        processed_content.processing_tier == 'ocr_required' or
        processed_content.contains_sensitive_content or
        processed_content.structure_unclear
    )
```

### Next Steps
1. Implement proof-of-concept with unstructured.io
2. Benchmark accuracy against sample document set
3. Develop quality scoring methodology
4. Create processing tier decision logic
5. Implement monitoring and alerting for processing failures
