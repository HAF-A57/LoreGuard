## JSON Schema Validation Research for LLM Outputs

### Executive Summary
For LoreGuard's evaluation pipeline, we need robust JSON schema validation to ensure structured LLM outputs are properly formatted, complete, and valid. Based on research, **Pydantic v2** emerges as the recommended solution for Python-based validation, with **jsonschema** as a lightweight alternative and **TypeScript schema validation** for frontend validation.

### Technology Comparison

#### Pydantic v2 (Recommended)
**Strengths:**
- **Performance**: 5-50x faster than Pydantic v1, competitive with pure JSON validation
- **Type Safety**: Full Python type hints integration with runtime validation
- **Rich Validation**: Complex validation rules, custom validators, field dependencies
- **Error Messages**: Detailed, user-friendly error messages with field paths
- **Serialization**: Built-in JSON serialization with custom encoders
- **OpenAI Integration**: Native support for OpenAI function calling schemas
- **Documentation**: Automatic schema generation for API documentation

**Architecture:**
```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Dict, List, Literal, Optional
from enum import Enum

class EvaluationLabel(str, Enum):
    SIGNAL = "Signal"
    NOISE = "Noise" 
    REVIEW = "Review"

class CategoryScore(BaseModel):
    score: float = Field(..., ge=0, le=5, description="Score from 0-5")
    reasoning: str = Field(..., min_length=10, description="Reasoning for this score")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in this score")

class EvaluationResult(BaseModel):
    """Structured evaluation result from LLM"""
    
    # Core evaluation
    scores: Dict[str, CategoryScore] = Field(
        ..., 
        description="Scores for each evaluation category"
    )
    overall_score: float = Field(..., ge=0, le=5, description="Weighted overall score")
    label: EvaluationLabel = Field(..., description="Final classification label")
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence")
    
    # Supporting information
    reasoning: str = Field(..., min_length=50, description="Overall reasoning")
    key_factors: List[str] = Field(..., min_items=1, description="Key evaluation factors")
    concerns: Optional[List[str]] = Field(None, description="Any concerns or limitations")
    
    # Metadata
    rubric_version: str = Field(..., description="Version of rubric used")
    model_id: str = Field(..., description="LLM model used for evaluation")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

    @validator('scores')
    def validate_required_categories(cls, v):
        required_categories = {'credibility', 'relevance', 'rigor', 'timeliness'}
        if not required_categories.issubset(v.keys()):
            missing = required_categories - v.keys()
            raise ValueError(f"Missing required categories: {missing}")
        return v

    @root_validator
    def validate_overall_score(cls, values):
        scores = values.get('scores', {})
        if scores:
            # Calculate weighted average (weights could be configurable)
            weights = {'credibility': 0.3, 'relevance': 0.3, 'rigor': 0.15, 'timeliness': 0.25}
            calculated_score = sum(
                scores[cat].score * weights.get(cat, 0) 
                for cat in scores.keys() 
                if cat in weights
            )
            
            overall = values.get('overall_score')
            if overall and abs(overall - calculated_score) > 0.1:
                raise ValueError(f"Overall score {overall} doesn't match calculated score {calculated_score:.2f}")
        
        return values

    @validator('label')
    def validate_label_score_consistency(cls, v, values):
        overall_score = values.get('overall_score')
        if overall_score:
            if v == EvaluationLabel.SIGNAL and overall_score < 3.8:
                raise ValueError("Signal label requires overall score >= 3.8")
            elif v == EvaluationLabel.NOISE and overall_score > 2.8:
                raise ValueError("Noise label requires overall score <= 2.8")
        return v
```

**Usage in LoreGuard:**
```python
# LLM evaluation service with Pydantic validation
import openai
from pydantic import ValidationError

class LLMEvaluationService:
    def __init__(self):
        self.client = openai.OpenAI()
        
    async def evaluate_artifact(self, artifact: Artifact, rubric: Rubric) -> EvaluationResult:
        """Evaluate artifact using LLM with structured output validation"""
        
        # Create OpenAI function schema from Pydantic model
        function_schema = {
            "name": "evaluate_document",
            "description": "Evaluate a document using the specified rubric",
            "parameters": EvaluationResult.schema()
        }
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._build_system_prompt(rubric)},
                    {"role": "user", "content": self._build_evaluation_prompt(artifact)}
                ],
                functions=[function_schema],
                function_call={"name": "evaluate_document"},
                temperature=0.1
            )
            
            # Extract function call arguments
            function_call = response.choices[0].message.function_call
            raw_result = json.loads(function_call.arguments)
            
            # Validate with Pydantic
            evaluation = EvaluationResult(**raw_result)
            
            # Add metadata
            evaluation.model_id = response.model
            evaluation.processing_time = response.usage.total_tokens / 1000  # Rough estimate
            
            return evaluation
            
        except ValidationError as e:
            # Handle validation errors gracefully
            logger.error(f"LLM output validation failed: {e}")
            
            # Could implement retry logic or fallback to human review
            raise EvaluationValidationError(f"Invalid LLM response: {e}")
        
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            raise EvaluationError(f"Evaluation failed: {e}")
```

#### Alternative: jsonschema Library
**Strengths:**
- **Lightweight**: Minimal dependencies, small footprint
- **Standard Compliant**: Full JSON Schema Draft 7/2019-09/2020-12 support
- **Language Agnostic**: JSON Schema can be used across languages
- **Flexible**: Works with any JSON data structure

**Weaknesses:**
- **Less Pythonic**: No native Python type integration
- **Basic Error Messages**: Less detailed error reporting
- **No Serialization**: Validation only, no data transformation
- **Manual Schema**: Requires hand-written JSON schemas

**Implementation:**
```python
import jsonschema
from jsonschema import validate, ValidationError

# JSON Schema definition
evaluation_schema = {
    "type": "object",
    "required": ["scores", "overall_score", "label", "confidence", "reasoning"],
    "properties": {
        "scores": {
            "type": "object",
            "required": ["credibility", "relevance", "rigor", "timeliness"],
            "properties": {
                "credibility": {
                    "type": "object",
                    "required": ["score", "reasoning", "confidence"],
                    "properties": {
                        "score": {"type": "number", "minimum": 0, "maximum": 5},
                        "reasoning": {"type": "string", "minLength": 10},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
                # ... other categories
            }
        },
        "overall_score": {"type": "number", "minimum": 0, "maximum": 5},
        "label": {"type": "string", "enum": ["Signal", "Noise", "Review"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning": {"type": "string", "minLength": 50}
    }
}

def validate_evaluation_result(data: dict) -> dict:
    """Validate LLM evaluation result against JSON schema"""
    try:
        validate(instance=data, schema=evaluation_schema)
        return data
    except ValidationError as e:
        raise ValueError(f"Validation failed: {e.message} at {e.absolute_path}")
```

#### Frontend Validation: Zod (TypeScript)
**For React/TypeScript frontend validation:**
```typescript
import { z } from 'zod'

const CategoryScoreSchema = z.object({
  score: z.number().min(0).max(5),
  reasoning: z.string().min(10),
  confidence: z.number().min(0).max(1)
})

const EvaluationResultSchema = z.object({
  scores: z.record(CategoryScoreSchema),
  overall_score: z.number().min(0).max(5),
  label: z.enum(['Signal', 'Noise', 'Review']),
  confidence: z.number().min(0).max(1),
  reasoning: z.string().min(50),
  key_factors: z.array(z.string()).min(1),
  concerns: z.array(z.string()).optional(),
  rubric_version: z.string(),
  model_id: z.string(),
  processing_time: z.number().optional()
}).refine(data => {
  // Custom validation logic
  const requiredCategories = ['credibility', 'relevance', 'rigor', 'timeliness']
  return requiredCategories.every(cat => cat in data.scores)
}, {
  message: "Missing required evaluation categories"
})

type EvaluationResult = z.infer<typeof EvaluationResultSchema>

// Usage in React component
const EvaluationDisplay = ({ rawData }: { rawData: unknown }) => {
  try {
    const evaluation = EvaluationResultSchema.parse(rawData)
    return <EvaluationResultComponent evaluation={evaluation} />
  } catch (error) {
    if (error instanceof z.ZodError) {
      return <ValidationErrorDisplay errors={error.errors} />
    }
    throw error
  }
}
```

### Advanced Validation Patterns

#### Custom Validators for Domain Logic
```python
from pydantic import validator, root_validator
from typing import Dict, Any

class RubricAwareEvaluationResult(EvaluationResult):
    """Evaluation result with rubric-specific validation"""
    
    @validator('scores', pre=True)
    def validate_against_rubric(cls, v, values):
        """Validate scores against loaded rubric configuration"""
        rubric_version = values.get('rubric_version')
        if rubric_version:
            rubric = load_rubric(rubric_version)
            
            # Check all required categories are present
            required_cats = set(rubric.categories.keys())
            provided_cats = set(v.keys())
            
            if not required_cats.issubset(provided_cats):
                missing = required_cats - provided_cats
                raise ValueError(f"Missing categories for rubric {rubric_version}: {missing}")
            
            # Validate category-specific constraints
            for cat_name, score_data in v.items():
                if cat_name in rubric.categories:
                    category = rubric.categories[cat_name]
                    
                    # Check subcriteria if defined
                    if hasattr(category, 'subcriteria') and category.subcriteria:
                        # Could validate subcriteria scoring here
                        pass
        
        return v

    @root_validator
    def validate_business_rules(cls, values):
        """Apply LoreGuard-specific business rules"""
        
        # Rule: Signal documents must have high credibility AND relevance
        label = values.get('label')
        scores = values.get('scores', {})
        
        if label == 'Signal':
            cred_score = scores.get('credibility', {}).get('score', 0)
            rel_score = scores.get('relevance', {}).get('score', 0)
            
            if cred_score < 3.5 or rel_score < 3.8:
                raise ValueError(
                    f"Signal label requires credibility >= 3.5 and relevance >= 3.8, "
                    f"got credibility={cred_score}, relevance={rel_score}"
                )
        
        # Rule: Low confidence should trigger human review
        confidence = values.get('confidence', 1.0)
        if confidence < 0.7 and label != 'Review':
            values['label'] = 'Review'  # Force human review for low confidence
            
        return values
```

#### Batch Validation for Performance
```python
from typing import List
from pydantic import ValidationError

class BatchEvaluationValidator:
    """Efficient batch validation for multiple evaluation results"""
    
    def __init__(self):
        self.schema = EvaluationResult.schema()
        
    def validate_batch(self, raw_results: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Validate multiple evaluation results efficiently"""
        
        validated_results = []
        validation_errors = []
        
        for i, raw_result in enumerate(raw_results):
            try:
                result = EvaluationResult(**raw_result)
                validated_results.append(result)
            except ValidationError as e:
                validation_errors.append({
                    'index': i,
                    'artifact_id': raw_result.get('artifact_id'),
                    'errors': e.errors()
                })
        
        if validation_errors:
            # Log validation errors for monitoring
            logger.warning(f"Batch validation failed for {len(validation_errors)} items")
            for error in validation_errors:
                logger.error(f"Validation error at index {error['index']}: {error['errors']}")
        
        return validated_results, validation_errors
```

#### Integration with OpenAI Structured Outputs
```python
# OpenAI function calling with Pydantic schema generation
def create_openai_function_schema(pydantic_model: type[BaseModel]) -> dict:
    """Convert Pydantic model to OpenAI function schema"""
    
    schema = pydantic_model.schema()
    
    # Convert Pydantic schema to OpenAI function format
    function_schema = {
        "name": "structured_response",
        "description": schema.get("description", "Structured response"),
        "parameters": {
            "type": "object",
            "properties": schema["properties"],
            "required": schema.get("required", [])
        }
    }
    
    return function_schema

# Usage in evaluation service
async def get_structured_evaluation(self, prompt: str) -> EvaluationResult:
    """Get structured evaluation using OpenAI function calling"""
    
    function_schema = create_openai_function_schema(EvaluationResult)
    
    response = await self.client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        functions=[function_schema],
        function_call={"name": "structured_response"}
    )
    
    # Parse and validate response
    raw_data = json.loads(response.choices[0].message.function_call.arguments)
    return EvaluationResult(**raw_data)  # Automatic validation
```

### Error Handling and Recovery

#### Graceful Degradation
```python
from enum import Enum

class ValidationSeverity(Enum):
    ERROR = "error"      # Block processing
    WARNING = "warning"  # Log but continue
    INFO = "info"       # Informational only

class ValidationResult:
    def __init__(self, is_valid: bool, data: Any = None, errors: List = None):
        self.is_valid = is_valid
        self.data = data
        self.errors = errors or []

def validate_with_fallback(raw_data: dict) -> ValidationResult:
    """Validate with graceful fallback strategies"""
    
    try:
        # Try full validation first
        result = EvaluationResult(**raw_data)
        return ValidationResult(True, result)
        
    except ValidationError as e:
        # Analyze errors and attempt recovery
        errors = e.errors()
        
        # Check if errors are recoverable
        recoverable_errors = []
        blocking_errors = []
        
        for error in errors:
            if error['type'] in ['missing', 'value_error.missing']:
                # Try to provide defaults for missing fields
                recoverable_errors.append(error)
            elif error['type'] in ['type_error', 'value_error.number.not_ge']:
                # Type/range errors are usually blocking
                blocking_errors.append(error)
            else:
                recoverable_errors.append(error)
        
        if not blocking_errors:
            # Attempt to fix recoverable errors
            fixed_data = apply_fixes(raw_data, recoverable_errors)
            try:
                result = EvaluationResult(**fixed_data)
                return ValidationResult(True, result, recoverable_errors)
            except ValidationError:
                pass
        
        # Validation failed, return partial result for human review
        return ValidationResult(False, raw_data, errors)

def apply_fixes(data: dict, errors: List[dict]) -> dict:
    """Apply automatic fixes for common validation errors"""
    
    fixed_data = data.copy()
    
    for error in errors:
        field_path = '.'.join(str(p) for p in error['loc'])
        
        if error['type'] == 'missing':
            # Provide sensible defaults for missing fields
            if 'confidence' in field_path:
                set_nested_value(fixed_data, error['loc'], 0.5)
            elif 'reasoning' in field_path:
                set_nested_value(fixed_data, error['loc'], "No reasoning provided")
        
        elif error['type'] == 'value_error.number.not_ge':
            # Clamp numbers to valid ranges
            if 'score' in field_path:
                current_value = get_nested_value(fixed_data, error['loc'])
                clamped_value = max(0, min(5, current_value))
                set_nested_value(fixed_data, error['loc'], clamped_value)
    
    return fixed_data
```

### Performance Optimization

#### Compiled Validation
```python
from pydantic import BaseModel
from typing import Dict, Any
import json

class OptimizedEvaluationValidator:
    """High-performance validator for evaluation results"""
    
    def __init__(self):
        # Pre-compile validation logic
        self._model = EvaluationResult
        self._schema = self._model.schema()
        
        # Cache common validation patterns
        self._required_fields = set(self._schema.get('required', []))
        self._field_types = {
            name: prop.get('type') 
            for name, prop in self._schema.get('properties', {}).items()
        }
    
    def validate_fast(self, data: Dict[str, Any]) -> EvaluationResult:
        """Fast path validation for performance-critical scenarios"""
        
        # Quick checks first
        if not self._required_fields.issubset(data.keys()):
            missing = self._required_fields - data.keys()
            raise ValueError(f"Missing required fields: {missing}")
        
        # Type checks
        for field, expected_type in self._field_types.items():
            if field in data:
                value = data[field]
                if expected_type == 'number' and not isinstance(value, (int, float)):
                    raise ValueError(f"Field {field} must be a number, got {type(value)}")
                elif expected_type == 'string' and not isinstance(value, str):
                    raise ValueError(f"Field {field} must be a string, got {type(value)}")
        
        # Full Pydantic validation
        return self._model(**data)

# Usage
validator = OptimizedEvaluationValidator()

# In tight loop processing thousands of evaluations
for raw_result in batch_results:
    try:
        evaluation = validator.validate_fast(raw_result)
        process_evaluation(evaluation)
    except ValueError as e:
        handle_validation_error(raw_result, e)
```

### Monitoring and Observability

#### Validation Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics for validation performance
validation_attempts = Counter('loreguard_validation_attempts_total', 'Total validation attempts', ['model', 'result'])
validation_errors = Counter('loreguard_validation_errors_total', 'Validation errors', ['error_type', 'field'])
validation_duration = Histogram('loreguard_validation_duration_seconds', 'Validation duration')

class MonitoredValidator:
    def __init__(self):
        self.validator = EvaluationResult
        
    def validate_with_monitoring(self, data: dict, model_id: str) -> EvaluationResult:
        """Validate with monitoring and metrics collection"""
        
        with validation_duration.time():
            try:
                result = self.validator(**data)
                validation_attempts.labels(model=model_id, result='success').inc()
                return result
                
            except ValidationError as e:
                validation_attempts.labels(model=model_id, result='error').inc()
                
                # Track specific error types
                for error in e.errors():
                    error_type = error['type']
                    field_path = '.'.join(str(p) for p in error['loc'])
                    validation_errors.labels(error_type=error_type, field=field_path).inc()
                
                raise
```

### Next Steps
1. **Implement Pydantic models** for all LoreGuard structured outputs
2. **Create validation middleware** for API endpoints
3. **Add error recovery strategies** for common validation failures  
4. **Implement batch validation** for performance
5. **Add monitoring and alerting** for validation failures

### Open Questions Resolved
- [x] **Primary Validation Library**: Pydantic v2 for Python backend
- [x] **Frontend Validation**: Zod for TypeScript/React
- [x] **Error Handling**: Graceful degradation with automatic fixes
- [x] **Performance Strategy**: Compiled validation with caching
- [x] **OpenAI Integration**: Function calling schema generation from Pydantic models
