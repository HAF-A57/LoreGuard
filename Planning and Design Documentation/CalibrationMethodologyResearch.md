## Calibration Methodology and Human Gold-Set Research

### Executive Summary
For LoreGuard's evaluation pipeline to maintain accuracy and credibility, we need robust calibration methodologies that compare LLM evaluations against human expert judgments. Based on research, **stratified sampling + inter-rater reliability + active learning** emerges as the recommended approach for creating and maintaining high-quality gold standard datasets.

### Calibration Framework Overview

#### Core Components
1. **Gold Standard Creation**: Human expert annotations across diverse document types
2. **Inter-Rater Reliability**: Statistical validation of annotation quality
3. **Drift Detection**: Monitoring for evaluation quality degradation over time
4. **Active Learning**: Intelligent selection of documents for human review
5. **Continuous Calibration**: Regular model retraining and threshold adjustment

### Human Gold Standard Dataset Creation

#### Stratified Sampling Strategy
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from typing import Dict, List
import numpy as np

class GoldStandardSampler:
    def __init__(self):
        self.stratification_criteria = [
            'source_type',      # Government, academic, think tank, media
            'document_type',    # Report, paper, article, brief
            'topic_category',   # Military, diplomatic, economic, information
            'language',         # English, Chinese, Russian, Arabic, etc.
            'publication_date', # Recent, historical
            'document_length'   # Short, medium, long
        ]
    
    def create_stratified_sample(self, artifact_pool: List[dict], 
                               sample_size: int = 1000) -> Dict[str, List[dict]]:
        """Create stratified sample for human annotation"""
        
        df = pd.DataFrame(artifact_pool)
        
        # Define strata based on multiple criteria
        df['stratum'] = df.apply(self._assign_stratum, axis=1)
        
        # Calculate sample sizes per stratum
        stratum_counts = df['stratum'].value_counts()
        stratum_samples = {}
        
        for stratum, count in stratum_counts.items():
            # Proportional allocation with minimum per stratum
            proportion = count / len(df)
            stratum_sample_size = max(10, int(sample_size * proportion))
            stratum_samples[stratum] = stratum_sample_size
        
        # Sample from each stratum
        sampled_artifacts = {}
        for stratum, target_size in stratum_samples.items():
            stratum_data = df[df['stratum'] == stratum]
            
            if len(stratum_data) >= target_size:
                sample = stratum_data.sample(n=target_size, random_state=42)
            else:
                sample = stratum_data  # Use all if stratum is small
            
            sampled_artifacts[stratum] = sample.to_dict('records')
        
        return sampled_artifacts
    
    def _assign_stratum(self, row) -> str:
        """Assign document to stratum based on characteristics"""
        
        # Create compound stratum identifier
        source_type = self._categorize_source(row['source'])
        doc_type = self._categorize_document_type(row['title'], row.get('content', ''))
        topic = self._categorize_topic(row.get('topics', []))
        
        return f"{source_type}_{doc_type}_{topic}"
    
    def _categorize_source(self, source_url: str) -> str:
        """Categorize source type"""
        
        if any(domain in source_url for domain in ['.gov', '.mil', 'defense.gov']):
            return 'government'
        elif any(domain in source_url for domain in ['.edu', 'arxiv.org', 'researchgate']):
            return 'academic'
        elif any(domain in source_url for domain in ['rand.org', 'csis.org', 'brookings']):
            return 'thinktank'
        else:
            return 'media'
```

#### Annotation Interface and Workflow
```python
# Human annotation interface
class AnnotationWorkflow:
    def __init__(self):
        self.annotation_schema = {
            'credibility': {
                'scale': (0, 5),
                'criteria': [
                    'Author expertise and reputation',
                    'Institutional affiliation quality',
                    'Publication venue credibility',
                    'Citation and peer review evidence'
                ],
                'guidelines': 'Evaluate based on verifiable credentials and institutional standing'
            },
            'relevance': {
                'scale': (0, 5),
                'criteria': [
                    'Alignment with AF wargaming scenarios',
                    'Operational applicability',
                    'Strategic importance',
                    'Temporal relevance'
                ],
                'guidelines': 'Score based on direct applicability to current wargaming objectives'
            },
            'rigor': {
                'scale': (0, 5),
                'criteria': [
                    'Methodology transparency',
                    'Data quality and sources',
                    'Analytical soundness',
                    'Reproducibility'
                ],
                'guidelines': 'Assess methodological quality and analytical rigor'
            }
        }
    
    def create_annotation_task(self, artifact: dict, annotator_id: str) -> dict:
        """Create structured annotation task"""
        
        return {
            'task_id': f"annotation_{artifact['id']}_{annotator_id}",
            'artifact_id': artifact['id'],
            'annotator_id': annotator_id,
            'artifact_data': {
                'title': artifact['title'],
                'author': artifact.get('author', 'Unknown'),
                'source': artifact['source'],
                'abstract': artifact.get('abstract', ''),
                'full_text_preview': artifact.get('content', '')[:2000],  # First 2000 chars
                'metadata': artifact.get('metadata', {})
            },
            'annotation_schema': self.annotation_schema,
            'instructions': self._generate_instructions(artifact),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
    
    def _generate_instructions(self, artifact: dict) -> str:
        """Generate context-specific annotation instructions"""
        
        doc_type = artifact.get('document_type', 'document')
        source_type = artifact.get('source_type', 'unknown')
        
        base_instructions = f"""
Please evaluate this {doc_type} from a {source_type} source for its value in Air Force wargaming scenarios.

Consider the following in your evaluation:

1. **Credibility**: How trustworthy is this source and author?
2. **Relevance**: How applicable is this content to current AF wargaming needs?
3. **Rigor**: How sound is the methodology and analysis?
4. **Timeliness**: How current and actionable is this information?

For each category, provide:
- A score from 0-5 (where 5 is highest quality)
- Brief reasoning for your score
- Overall recommendation: Signal, Review, or Noise
"""
        
        return base_instructions
```

### Inter-Rater Reliability Measurement

#### Statistical Validation Methods
```python
import numpy as np
from scipy import stats
from sklearn.metrics import cohen_kappa_score
import krippendorff

class InterRaterReliabilityAnalyzer:
    def __init__(self):
        self.reliability_thresholds = {
            'excellent': 0.8,
            'good': 0.6,
            'moderate': 0.4,
            'poor': 0.2
        }
    
    def calculate_inter_rater_reliability(self, annotations: List[dict]) -> dict:
        """Calculate comprehensive inter-rater reliability metrics"""
        
        # Organize annotations by artifact and annotator
        annotation_matrix = self._build_annotation_matrix(annotations)
        
        reliability_metrics = {}
        
        # Cohen's Kappa (for pairs of annotators)
        if len(annotation_matrix.columns) >= 2:
            kappa_scores = self._calculate_pairwise_kappa(annotation_matrix)
            reliability_metrics['cohen_kappa'] = {
                'mean': np.mean(kappa_scores),
                'std': np.std(kappa_scores),
                'min': np.min(kappa_scores),
                'max': np.max(kappa_scores)
            }
        
        # Krippendorff's Alpha (for multiple annotators)
        if len(annotation_matrix.columns) >= 3:
            alpha_score = self._calculate_krippendorff_alpha(annotation_matrix)
            reliability_metrics['krippendorff_alpha'] = alpha_score
        
        # Intraclass Correlation Coefficient
        icc_score = self._calculate_icc(annotation_matrix)
        reliability_metrics['icc'] = icc_score
        
        # Overall reliability assessment
        reliability_metrics['assessment'] = self._assess_reliability(reliability_metrics)
        
        return reliability_metrics
    
    def _build_annotation_matrix(self, annotations: List[dict]) -> pd.DataFrame:
        """Build matrix of annotations for reliability analysis"""
        
        # Create pivot table: artifacts x annotators
        df = pd.DataFrame(annotations)
        
        # For each category, create separate reliability analysis
        categories = ['credibility', 'relevance', 'rigor', 'timeliness', 'overall_score']
        
        matrices = {}
        for category in categories:
            if category in df.columns:
                matrix = df.pivot_table(
                    values=category,
                    index='artifact_id',
                    columns='annotator_id',
                    aggfunc='first'
                )
                matrices[category] = matrix
        
        return matrices
    
    def _calculate_pairwise_kappa(self, annotation_matrix: pd.DataFrame) -> List[float]:
        """Calculate Cohen's Kappa for all pairs of annotators"""
        
        kappa_scores = []
        annotators = annotation_matrix.columns
        
        for i in range(len(annotators)):
            for j in range(i + 1, len(annotators)):
                ann1 = annotators[i]
                ann2 = annotators[j]
                
                # Get common annotations (both annotators rated)
                common_mask = annotation_matrix[ann1].notna() & annotation_matrix[ann2].notna()
                
                if common_mask.sum() >= 10:  # Minimum 10 common annotations
                    ratings1 = annotation_matrix.loc[common_mask, ann1]
                    ratings2 = annotation_matrix.loc[common_mask, ann2]
                    
                    # Convert continuous scores to ordinal categories for kappa
                    cat1 = self._discretize_scores(ratings1)
                    cat2 = self._discretize_scores(ratings2)
                    
                    kappa = cohen_kappa_score(cat1, cat2)
                    kappa_scores.append(kappa)
        
        return kappa_scores
    
    def _calculate_krippendorff_alpha(self, annotation_matrix: pd.DataFrame) -> float:
        """Calculate Krippendorff's Alpha for multiple annotators"""
        
        # Convert to format expected by krippendorff library
        # (annotators x artifacts)
        reliability_data = annotation_matrix.T.values
        
        try:
            alpha = krippendorff.alpha(
                reliability_data,
                level_of_measurement='interval'  # Continuous scores
            )
            return alpha
        except Exception as e:
            logger.warning(f"Krippendorff's Alpha calculation failed: {e}")
            return 0.0
    
    def _discretize_scores(self, scores: pd.Series) -> List[str]:
        """Convert continuous scores to ordinal categories"""
        
        categories = []
        for score in scores:
            if score >= 4.5:
                categories.append('excellent')
            elif score >= 3.5:
                categories.append('good')
            elif score >= 2.5:
                categories.append('moderate')
            elif score >= 1.5:
                categories.append('poor')
            else:
                categories.append('very_poor')
        
        return categories
```

### Active Learning for Efficient Annotation

#### Uncertainty Sampling
```python
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

class ActiveLearningAnnotationSelector:
    def __init__(self):
        self.selection_strategies = [
            'uncertainty_sampling',
            'diversity_sampling',
            'disagreement_sampling',
            'confidence_sampling'
        ]
    
    def select_documents_for_annotation(self, candidate_pool: List[dict], 
                                      current_annotations: List[dict],
                                      target_count: int = 50) -> List[dict]:
        """Select most valuable documents for human annotation"""
        
        # Strategy 1: Uncertainty sampling (low confidence predictions)
        uncertainty_candidates = self._select_by_uncertainty(candidate_pool, target_count // 4)
        
        # Strategy 2: Diversity sampling (representative coverage)
        diversity_candidates = self._select_by_diversity(candidate_pool, target_count // 4)
        
        # Strategy 3: Disagreement sampling (high model disagreement)
        disagreement_candidates = self._select_by_disagreement(candidate_pool, target_count // 4)
        
        # Strategy 4: Edge case sampling (boundary conditions)
        edge_candidates = self._select_edge_cases(candidate_pool, target_count // 4)
        
        # Combine and deduplicate
        selected_ids = set()
        selected_documents = []
        
        for candidate_list in [uncertainty_candidates, diversity_candidates, 
                             disagreement_candidates, edge_candidates]:
            for doc in candidate_list:
                if doc['id'] not in selected_ids:
                    selected_ids.add(doc['id'])
                    selected_documents.append(doc)
        
        return selected_documents[:target_count]
    
    def _select_by_uncertainty(self, candidates: List[dict], count: int) -> List[dict]:
        """Select documents with lowest evaluation confidence"""
        
        # Sort by confidence (ascending - lowest confidence first)
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: x.get('evaluation', {}).get('confidence', 1.0)
        )
        
        return sorted_candidates[:count]
    
    def _select_by_diversity(self, candidates: List[dict], count: int) -> List[dict]:
        """Select documents for maximum diversity coverage"""
        
        # Extract text features for clustering
        texts = [doc.get('content', doc.get('title', '')) for doc in candidates]
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        text_vectors = vectorizer.fit_transform(texts)
        
        # K-means clustering
        n_clusters = min(count, len(candidates))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(text_vectors)
        
        # Select one document from each cluster (closest to centroid)
        selected = []
        for cluster_id in range(n_clusters):
            cluster_mask = clusters == cluster_id
            cluster_docs = [candidates[i] for i in range(len(candidates)) if cluster_mask[i]]
            
            if cluster_docs:
                # Select document closest to cluster centroid
                cluster_vectors = text_vectors[cluster_mask]
                centroid = cluster_vectors.mean(axis=0)
                
                distances = [
                    np.linalg.norm(cluster_vectors[i] - centroid)
                    for i in range(cluster_vectors.shape[0])
                ]
                
                closest_idx = np.argmin(distances)
                selected.append(cluster_docs[closest_idx])
        
        return selected
    
    def _select_by_disagreement(self, candidates: List[dict], count: int) -> List[dict]:
        """Select documents where multiple models disagree"""
        
        # Calculate disagreement score based on evaluation variance
        disagreement_scores = []
        
        for doc in candidates:
            evaluations = doc.get('multiple_evaluations', [])
            
            if len(evaluations) >= 2:
                scores = [eval_result.get('overall_score', 0) for eval_result in evaluations]
                disagreement = np.var(scores)  # Higher variance = more disagreement
                disagreement_scores.append((doc, disagreement))
        
        # Sort by disagreement (descending)
        disagreement_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, _ in disagreement_scores[:count]]
```

### Calibration Metrics and Monitoring

#### Performance Tracking
```python
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

class CalibrationMonitor:
    def __init__(self):
        self.metrics_history = []
        self.drift_thresholds = {
            'precision_drop': 0.05,
            'recall_drop': 0.05,
            'f1_drop': 0.05,
            'confidence_shift': 0.1
        }
    
    def evaluate_model_performance(self, human_labels: List[str], 
                                 model_predictions: List[dict]) -> dict:
        """Evaluate model performance against human gold standard"""
        
        # Extract model labels and confidence scores
        model_labels = [pred['label'] for pred in model_predictions]
        model_confidences = [pred['confidence'] for pred in model_predictions]
        model_scores = [pred['overall_score'] for pred in model_predictions]
        
        # Calculate classification metrics
        precision, recall, f1, support = precision_recall_fscore_support(
            human_labels, model_labels, average='weighted'
        )
        
        # Calculate per-class metrics
        per_class_metrics = {}
        for label in ['Signal', 'Noise', 'Review']:
            if label in human_labels and label in model_labels:
                label_precision, label_recall, label_f1, _ = precision_recall_fscore_support(
                    [1 if l == label else 0 for l in human_labels],
                    [1 if l == label else 0 for l in model_labels],
                    average='binary'
                )
                per_class_metrics[label] = {
                    'precision': label_precision,
                    'recall': label_recall,
                    'f1': label_f1
                }
        
        # Confidence calibration analysis
        confidence_calibration = self._analyze_confidence_calibration(
            human_labels, model_labels, model_confidences
        )
        
        # Score correlation analysis
        score_correlation = self._analyze_score_correlation(
            human_labels, model_scores
        )
        
        metrics = {
            'overall_metrics': {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'accuracy': sum(h == m for h, m in zip(human_labels, model_labels)) / len(human_labels)
            },
            'per_class_metrics': per_class_metrics,
            'confidence_calibration': confidence_calibration,
            'score_correlation': score_correlation,
            'evaluation_timestamp': datetime.utcnow().isoformat()
        }
        
        # Store metrics for drift detection
        self.metrics_history.append(metrics)
        
        return metrics
    
    def _analyze_confidence_calibration(self, human_labels: List[str], 
                                      model_labels: List[str], 
                                      confidences: List[float]) -> dict:
        """Analyze how well model confidence correlates with accuracy"""
        
        # Calculate accuracy per confidence bin
        confidence_bins = np.linspace(0, 1, 11)  # 10 bins
        bin_accuracies = []
        bin_confidences = []
        bin_counts = []
        
        for i in range(len(confidence_bins) - 1):
            bin_mask = (np.array(confidences) >= confidence_bins[i]) & \
                      (np.array(confidences) < confidence_bins[i + 1])
            
            if bin_mask.sum() > 0:
                bin_human = [human_labels[j] for j in range(len(human_labels)) if bin_mask[j]]
                bin_model = [model_labels[j] for j in range(len(model_labels)) if bin_mask[j]]
                bin_conf = [confidences[j] for j in range(len(confidences)) if bin_mask[j]]
                
                accuracy = sum(h == m for h, m in zip(bin_human, bin_model)) / len(bin_human)
                avg_confidence = np.mean(bin_conf)
                
                bin_accuracies.append(accuracy)
                bin_confidences.append(avg_confidence)
                bin_counts.append(len(bin_human))
        
        # Calculate calibration error
        calibration_error = np.mean([
            abs(acc - conf) for acc, conf in zip(bin_accuracies, bin_confidences)
        ])
        
        return {
            'calibration_error': calibration_error,
            'bin_accuracies': bin_accuracies,
            'bin_confidences': bin_confidences,
            'bin_counts': bin_counts,
            'is_well_calibrated': calibration_error < 0.1
        }
    
    def detect_performance_drift(self) -> dict:
        """Detect if model performance has degraded over time"""
        
        if len(self.metrics_history) < 2:
            return {'drift_detected': False, 'reason': 'Insufficient history'}
        
        # Compare latest metrics with baseline (first evaluation)
        baseline = self.metrics_history[0]['overall_metrics']
        latest = self.metrics_history[-1]['overall_metrics']
        
        drift_indicators = {}
        
        # Check for significant drops in key metrics
        for metric in ['precision', 'recall', 'f1_score']:
            drop = baseline[metric] - latest[metric]
            threshold = self.drift_thresholds[f'{metric[:-6] if metric.endswith("_score") else metric}_drop']
            
            drift_indicators[f'{metric}_drift'] = {
                'baseline': baseline[metric],
                'current': latest[metric],
                'drop': drop,
                'significant': drop > threshold
            }
        
        # Overall drift assessment
        significant_drifts = [k for k, v in drift_indicators.items() if v['significant']]
        
        return {
            'drift_detected': len(significant_drifts) > 0,
            'significant_drifts': significant_drifts,
            'drift_indicators': drift_indicators,
            'recommendation': self._generate_drift_recommendation(significant_drifts)
        }
    
    def _generate_drift_recommendation(self, significant_drifts: List[str]) -> str:
        """Generate recommendation based on detected drift"""
        
        if not significant_drifts:
            return "No action needed - model performance is stable"
        elif len(significant_drifts) == 1:
            return f"Monitor {significant_drifts[0]} - consider targeted retraining"
        else:
            return "Multiple performance drops detected - recommend comprehensive recalibration"
```

### Continuous Calibration Pipeline

#### Automated Calibration Workflow
```python
from temporalio import workflow, activity

@workflow.defn
class CalibrationWorkflow:
    @workflow.run
    async def run(self, calibration_config: CalibrationConfig) -> CalibrationResult:
        """Automated calibration workflow"""
        
        # Step 1: Select documents for human annotation
        annotation_candidates = await workflow.execute_activity(
            select_annotation_candidates,
            calibration_config.selection_criteria,
            start_to_close_timeout=timedelta(minutes=30)
        )
        
        # Step 2: Distribute to human annotators
        annotation_tasks = await workflow.execute_activity(
            create_annotation_tasks,
            annotation_candidates,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Step 3: Wait for human annotations (with timeout)
        annotations = await workflow.execute_activity(
            collect_human_annotations,
            annotation_tasks,
            start_to_close_timeout=timedelta(days=7)  # 1 week for annotation
        )
        
        # Step 4: Calculate inter-rater reliability
        reliability_metrics = await workflow.execute_activity(
            calculate_reliability_metrics,
            annotations,
            start_to_close_timeout=timedelta(minutes=15)
        )
        
        # Step 5: Evaluate model performance
        performance_metrics = await workflow.execute_activity(
            evaluate_model_performance,
            annotations,
            start_to_close_timeout=timedelta(minutes=30)
        )
        
        # Step 6: Detect drift and recommend actions
        drift_analysis = await workflow.execute_activity(
            analyze_performance_drift,
            performance_metrics,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Step 7: Update thresholds if needed
        if drift_analysis['drift_detected']:
            threshold_updates = await workflow.execute_activity(
                recommend_threshold_updates,
                drift_analysis,
                start_to_close_timeout=timedelta(minutes=20)
            )
        else:
            threshold_updates = None
        
        return CalibrationResult(
            reliability_metrics=reliability_metrics,
            performance_metrics=performance_metrics,
            drift_analysis=drift_analysis,
            threshold_updates=threshold_updates,
            calibration_date=datetime.utcnow()
        )

@activity.defn
async def select_annotation_candidates(selection_criteria: dict) -> List[dict]:
    """Select documents for human annotation using active learning"""
    
    sampler = GoldStandardSampler()
    selector = ActiveLearningAnnotationSelector()
    
    # Get candidate pool
    candidate_pool = await get_unannotated_artifacts(selection_criteria)
    
    # Apply active learning selection
    selected_documents = selector.select_documents_for_annotation(
        candidate_pool,
        await get_existing_annotations(),
        target_count=selection_criteria.get('sample_size', 100)
    )
    
    return selected_documents
```

### Human Annotation Tools Integration

#### Annotation Interface
```python
# Streamlit-based annotation interface
import streamlit as st
import pandas as pd

class AnnotationInterface:
    def __init__(self):
        self.current_task = None
        self.annotator_id = None
    
    def render_annotation_interface(self):
        """Render web-based annotation interface"""
        
        st.title("LoreGuard Document Evaluation")
        
        # Annotator authentication
        if not st.session_state.get('annotator_id'):
            self._render_login()
            return
        
        # Load annotation task
        if not st.session_state.get('current_task'):
            self._load_next_task()
        
        task = st.session_state.get('current_task')
        if not task:
            st.success("No more documents to annotate!")
            return
        
        # Display document
        self._render_document_display(task)
        
        # Annotation form
        self._render_annotation_form(task)
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Previous"):
                self._load_previous_task()
        with col2:
            if st.button("Skip"):
                self._skip_current_task()
        with col3:
            if st.button("Submit & Next"):
                self._submit_annotation()
                self._load_next_task()
    
    def _render_document_display(self, task: dict):
        """Display document for annotation"""
        
        artifact = task['artifact_data']
        
        st.subheader(artifact['title'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Author:** {artifact['author']}")
            st.write(f"**Source:** {artifact['source']}")
        with col2:
            st.write(f"**Date:** {artifact.get('date', 'Unknown')}")
            st.write(f"**Type:** {artifact.get('document_type', 'Unknown')}")
        
        # Document preview
        with st.expander("Document Preview", expanded=True):
            st.text_area(
                "Content Preview",
                value=artifact['full_text_preview'],
                height=300,
                disabled=True
            )
    
    def _render_annotation_form(self, task: dict):
        """Render annotation form"""
        
        st.subheader("Evaluation")
        
        annotations = {}
        
        # Category evaluations
        for category, schema in task['annotation_schema'].items():
            st.write(f"**{category.title()}**")
            st.write(schema['guidelines'])
            
            # Score slider
            score = st.slider(
                f"{category} Score",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=2.5,
                key=f"score_{category}"
            )
            
            # Reasoning text
            reasoning = st.text_area(
                f"{category} Reasoning",
                placeholder="Explain your scoring rationale...",
                key=f"reasoning_{category}"
            )
            
            annotations[category] = {
                'score': score,
                'reasoning': reasoning
            }
        
        # Overall assessment
        st.subheader("Overall Assessment")
        
        overall_label = st.selectbox(
            "Final Classification",
            options=['Signal', 'Review', 'Noise'],
            help="Signal: High value for wargaming, Review: Needs expert review, Noise: Low value"
        )
        
        confidence = st.slider(
            "Confidence in Assessment",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=0.8
        )
        
        overall_comments = st.text_area(
            "Additional Comments",
            placeholder="Any additional observations or concerns..."
        )
        
        # Store annotations in session state
        st.session_state['current_annotations'] = {
            'category_scores': annotations,
            'overall_label': overall_label,
            'confidence': confidence,
            'comments': overall_comments,
            'annotator_id': st.session_state['annotator_id'],
            'annotation_time': datetime.utcnow().isoformat()
        }
```

### Quality Assurance and Validation

#### Gold Standard Validation
```python
class GoldStandardValidator:
    def __init__(self):
        self.validation_rules = [
            'completeness_check',
            'consistency_check',
            'outlier_detection',
            'bias_detection'
        ]
    
    def validate_annotation_quality(self, annotations: List[dict]) -> dict:
        """Validate quality of human annotations"""
        
        validation_results = {}
        
        # Completeness check
        validation_results['completeness'] = self._check_completeness(annotations)
        
        # Consistency check (within-annotator)
        validation_results['consistency'] = self._check_consistency(annotations)
        
        # Outlier detection
        validation_results['outliers'] = self._detect_outliers(annotations)
        
        # Bias detection
        validation_results['bias'] = self._detect_bias(annotations)
        
        # Overall quality score
        quality_factors = [
            validation_results['completeness']['score'],
            validation_results['consistency']['score'],
            1.0 - validation_results['outliers']['outlier_rate'],
            1.0 - validation_results['bias']['bias_score']
        ]
        
        overall_quality = np.mean(quality_factors)
        
        return {
            'validation_results': validation_results,
            'overall_quality': overall_quality,
            'quality_grade': self._grade_annotation_quality(overall_quality),
            'recommendations': self._generate_quality_recommendations(validation_results)
        }
    
    def _check_completeness(self, annotations: List[dict]) -> dict:
        """Check if annotations are complete"""
        
        required_fields = ['credibility', 'relevance', 'rigor', 'overall_label']
        
        completeness_scores = []
        for annotation in annotations:
            completed_fields = sum(
                1 for field in required_fields 
                if field in annotation and annotation[field] is not None
            )
            completeness = completed_fields / len(required_fields)
            completeness_scores.append(completeness)
        
        return {
            'mean_completeness': np.mean(completeness_scores),
            'min_completeness': np.min(completeness_scores),
            'incomplete_annotations': sum(1 for score in completeness_scores if score < 1.0),
            'score': np.mean(completeness_scores)
        }
    
    def _detect_outliers(self, annotations: List[dict]) -> dict:
        """Detect outlier annotations that may indicate quality issues"""
        
        # Extract numerical scores
        scores_by_category = {}
        for annotation in annotations:
            for category in ['credibility', 'relevance', 'rigor']:
                if category in annotation:
                    if category not in scores_by_category:
                        scores_by_category[category] = []
                    scores_by_category[category].append(annotation[category]['score'])
        
        outliers = []
        for category, scores in scores_by_category.items():
            if len(scores) >= 10:  # Need minimum sample size
                q1, q3 = np.percentile(scores, [25, 75])
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                category_outliers = [
                    i for i, score in enumerate(scores)
                    if score < lower_bound or score > upper_bound
                ]
                
                outliers.extend([(i, category, scores[i]) for i in category_outliers])
        
        return {
            'outlier_count': len(outliers),
            'outlier_rate': len(outliers) / len(annotations) if annotations else 0,
            'outlier_details': outliers
        }
```

### Next Steps
1. **Implement stratified sampling** for gold standard creation
2. **Build annotation interface** with Streamlit or web framework
3. **Set up inter-rater reliability** monitoring
4. **Create active learning pipeline** for efficient annotation
5. **Implement drift detection** and alerting system

### Open Questions Resolved
- [x] **Sampling Strategy**: Stratified sampling across document types and sources
- [x] **Reliability Metrics**: Cohen's Kappa + Krippendorff's Alpha + ICC
- [x] **Active Learning**: Uncertainty + diversity + disagreement sampling
- [x] **Annotation Interface**: Streamlit-based web interface with structured forms
- [x] **Quality Assurance**: Automated validation with outlier detection
- [x] **Drift Detection**: Statistical monitoring with automated alerting
