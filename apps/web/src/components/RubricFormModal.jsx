import { useState, useEffect } from 'react'
import { API_URL } from '@/config.js'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import {
  Plus,
  Trash2,
  Save,
  X,
  Loader2,
  AlertCircle,
  Target,
  Info
} from 'lucide-react'
import InfoTooltip from './InfoTooltip.jsx'

const RubricFormModal = ({ rubricId, open, onOpenChange, onSuccess }) => {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [promptTemplates, setPromptTemplates] = useState([])
  const [loadingTemplates, setLoadingTemplates] = useState(false)
  const [formData, setFormData] = useState({
    version: '',
    is_active: false,
    categories: [],
    thresholds: {
      signal_min: 3.5,
      review_min: 2.5,
      noise_max: 2.4
    },
    prompts: {
      metadata: '',
      evaluation: '',
      clarification: ''
    }
  })

  const isEditMode = !!rubricId

  // Fetch prompt templates when modal opens
  useEffect(() => {
    if (open) {
      fetchPromptTemplates()
    }
  }, [open])

  // Load rubric data when editing
  useEffect(() => {
    if (open && isEditMode && rubricId) {
      fetchRubric()
    } else if (open && !isEditMode) {
      // Reset form for new rubric
      setFormData({
        version: '',
        is_active: false,
        categories: [],
        thresholds: {
          signal_min: 3.5,
          review_min: 2.5,
          noise_max: 2.4
        },
        prompts: {
          metadata: '',
          evaluation: '',
          clarification: ''
        }
      })
      setError(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, rubricId, isEditMode])

  const fetchPromptTemplates = async () => {
    try {
      setLoadingTemplates(true)
      const response = await fetch(`${API_URL}/api/v1/prompt-templates/`)
      if (response.ok) {
        const data = await response.json()
        setPromptTemplates(data.items || [])
        // Set default templates for new rubrics if not in edit mode
        if (!isEditMode && data.items) {
          const metadataDefault = data.items.find(t => t.type === 'metadata' && t.is_default && t.is_active)
          const evaluationDefault = data.items.find(t => t.type === 'evaluation' && t.is_default && t.is_active)
          const clarificationDefault = data.items.find(t => t.type === 'clarification' && t.is_default && t.is_active)
          
          if (metadataDefault || evaluationDefault || clarificationDefault) {
            setFormData(prev => ({
              ...prev,
              prompts: {
                metadata: metadataDefault?.reference_id || '',
                evaluation: evaluationDefault?.reference_id || '',
                clarification: clarificationDefault?.reference_id || ''
              }
            }))
          }
        }
      }
    } catch (err) {
      console.error('Error fetching prompt templates:', err)
    } finally {
      setLoadingTemplates(false)
    }
  }

  const fetchRubric = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_URL}/api/v1/rubrics/${rubricId}`)
      if (!response.ok) throw new Error('Failed to fetch rubric')
      const data = await response.json()
      
      // Convert categories from array to array format (if needed) or keep as-is
      const categories = Array.isArray(data.categories) 
        ? data.categories 
        : Object.entries(data.categories || {}).map(([key, value]) => ({
            id: key,
            name: value.name || key,
            weight: value.weight || 0,
            description: value.guidance || value.description || '',
            criteria: value.subcriteria || value.criteria || [],
            scale: value.scale || { min: 0, max: 5 }
          }))
      
      setFormData({
        version: data.version || '',
        is_active: data.is_active || false,
        categories: categories,
        thresholds: data.thresholds || {
          signal_min: 3.5,
          review_min: 2.5,
          noise_max: 2.4
        },
        prompts: data.prompts || {
          metadata: '',
          evaluation: '',
          clarification: ''
        }
      })
    } catch (err) {
      console.error('Error fetching rubric:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const addCategory = () => {
    const newCategory = {
      id: `category_${Date.now()}`,
      name: '',
      weight: 0,
      description: '',
      criteria: [],
      scale: { min: 0, max: 5 }
    }
    setFormData({
      ...formData,
      categories: [...formData.categories, newCategory]
    })
  }

  const removeCategory = (index) => {
    setFormData({
      ...formData,
      categories: formData.categories.filter((_, i) => i !== index)
    })
  }

  const updateCategory = (index, field, value) => {
    const updated = [...formData.categories]
    updated[index] = { ...updated[index], [field]: value }
    setFormData({ ...formData, categories: updated })
  }

  const addCriterion = (categoryIndex) => {
    const updated = [...formData.categories]
    updated[categoryIndex].criteria = [...(updated[categoryIndex].criteria || []), '']
    setFormData({ ...formData, categories: updated })
  }

  const removeCriterion = (categoryIndex, criterionIndex) => {
    const updated = [...formData.categories]
    updated[categoryIndex].criteria = updated[categoryIndex].criteria.filter((_, i) => i !== criterionIndex)
    setFormData({ ...formData, categories: updated })
  }

  const updateCriterion = (categoryIndex, criterionIndex, value) => {
    const updated = [...formData.categories]
    updated[categoryIndex].criteria[criterionIndex] = value
    setFormData({ ...formData, categories: updated })
  }

  const calculateTotalWeight = () => {
    return formData.categories.reduce((sum, cat) => sum + (parseFloat(cat.weight) || 0), 0)
  }

  const validateForm = () => {
    if (!formData.version.trim()) {
      setError('Version is required')
      return false
    }
    if (formData.categories.length === 0) {
      setError('At least one category is required')
      return false
    }
    
    // Validate categories
    for (let i = 0; i < formData.categories.length; i++) {
      const cat = formData.categories[i]
      if (!cat.name.trim()) {
        setError(`Category ${i + 1} name is required`)
        return false
      }
      if (!cat.id.trim()) {
        setError(`Category ${i + 1} ID is required`)
        return false
      }
      if (cat.weight < 0 || cat.weight > 1) {
        setError(`Category ${i + 1} weight must be between 0 and 1`)
        return false
      }
    }
    
    // Validate weights sum to 1.0
    const totalWeight = calculateTotalWeight()
    if (Math.abs(totalWeight - 1.0) > 0.01) {
      setError(`Category weights must sum to 1.0 (currently ${totalWeight.toFixed(2)})`)
      return false
    }
    
    // Validate thresholds
    if (formData.thresholds.signal_min < formData.thresholds.review_min) {
      setError('Signal minimum must be >= Review minimum')
      return false
    }
    
    return true
  }

  const preparePayload = () => {
    // Convert categories array to dict format for API
    const categoriesDict = {}
    formData.categories.forEach(cat => {
      categoriesDict[cat.id] = {
        weight: parseFloat(cat.weight) || 0,
        guidance: cat.description || '',
        subcriteria: cat.criteria || [],
        scale: cat.scale || { min: 0, max: 5 }
      }
    })
    
    return {
      version: formData.version.trim(),
      is_active: formData.is_active,
      categories: categoriesDict,
      thresholds: {
        signal_min: parseFloat(formData.thresholds.signal_min) || 3.5,
        review_min: parseFloat(formData.thresholds.review_min) || 2.5,
        noise_max: parseFloat(formData.thresholds.noise_max) || 2.4
      },
      prompts: formData.prompts
    }
  }

  const handleSave = async () => {
    setError(null)
    if (!validateForm()) {
      return
    }
    
    try {
      setSaving(true)
      const payload = preparePayload()
      
      const url = isEditMode 
        ? `${API_URL}/api/v1/rubrics/${rubricId}`
        : `${API_URL}/api/v1/rubrics/`
      
      const method = isEditMode ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Failed to ${isEditMode ? 'update' : 'create'} rubric`)
      }
      
      const result = await response.json()
      onSuccess?.(result)
      onOpenChange(false)
    } catch (err) {
      console.error('Error saving rubric:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  const totalWeight = calculateTotalWeight()
  const weightError = Math.abs(totalWeight - 1.0) > 0.01

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[2400px] max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5" />
            <span>{isEditMode ? 'Edit Rubric' : 'Create New Rubric'}</span>
          </DialogTitle>
          <DialogDescription>
            {isEditMode ? 'Update rubric details and evaluation criteria' : 'Define a new evaluation rubric with categories, thresholds, and prompts'}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[calc(90vh-200px)] pr-4">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 mb-4">
              <div className="flex items-center space-x-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            </div>
          )}

          {!loading && (
            <div className="space-y-6">
              {/* Basic Information */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                  <CardDescription>Rubric version and activation status</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Label htmlFor="version">Version *</Label>
                        <InfoTooltip 
                          content="Unique identifier for this rubric version (e.g., v2.1). Used for tracking which rubric version was used for evaluations. This appears in the LLM system prompt."
                          llmBound={true}
                        />
                      </div>
                      <Input
                        id="version"
                        value={formData.version}
                        onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                        placeholder="e.g., v2.1"
                      />
                    </div>
                    <div className="space-y-2 flex items-end">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.is_active}
                          onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                          className="h-4 w-4"
                        />
                        <span className="text-sm font-medium">Set as active rubric</span>
                        <InfoTooltip 
                          content="When active, this rubric will be used by default for all new evaluations. Only one rubric can be active at a time. This is a configuration setting, not sent to the LLM."
                          llmBound={false}
                        />
                      </label>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Categories */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <CardTitle>Evaluation Categories</CardTitle>
                        <InfoTooltip 
                          content="Categories define the scoring dimensions for evaluation. Each category has a weight (0-1) that determines its importance. Categories, weights, guidance, and criteria are ALL sent to the LLM in the system prompt to guide scoring."
                          llmBound={true}
                        />
                      </div>
                      <CardDescription>
                        Define weighted scoring categories. Total weight: <span className={weightError ? 'text-destructive font-bold' : 'font-semibold'}>{totalWeight.toFixed(2)}</span> / 1.00
                      </CardDescription>
                    </div>
                    <Button onClick={addCategory} size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Category
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {formData.categories.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>No categories defined. Click "Add Category" to get started.</p>
                    </div>
                  ) : (
                    formData.categories.map((category, index) => (
                      <Card key={index} className="border-2">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-lg">Category {index + 1}</CardTitle>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => removeCategory(index)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <Label>Category ID *</Label>
                                <InfoTooltip 
                                  content="Unique identifier for this category (e.g., 'credibility'). Used as the key in the categories object sent to the LLM. Use lowercase with underscores (snake_case)."
                                  llmBound={true}
                                />
                              </div>
                              <Input
                                value={category.id}
                                onChange={(e) => updateCategory(index, 'id', e.target.value)}
                                placeholder="e.g., credibility"
                              />
                            </div>
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <Label>Category Name *</Label>
                                <InfoTooltip 
                                  content="Human-readable name for this category (e.g., 'Source Credibility'). Used for display purposes and may appear in LLM prompts for clarity."
                                  llmBound={true}
                                />
                              </div>
                              <Input
                                value={category.name}
                                onChange={(e) => updateCategory(index, 'name', e.target.value)}
                                placeholder="e.g., Source Credibility"
                              />
                            </div>
                          </div>
                          <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <Label>Weight (0-1) *</Label>
                                <InfoTooltip 
                                  content="Weight determines how much this category contributes to the total score. Must be between 0 and 1. All category weights must sum to exactly 1.0. This weight is used in the LLM system prompt and for calculating final scores."
                                  llmBound={true}
                                />
                              </div>
                              <Input
                                type="number"
                                step="0.01"
                                min="0"
                                max="1"
                                value={category.weight}
                                onChange={(e) => updateCategory(index, 'weight', parseFloat(e.target.value) || 0)}
                              />
                            </div>
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <Label>Scale Min</Label>
                                <InfoTooltip 
                                  content="Minimum score value for this category (typically 0). Defines the scoring range sent to the LLM."
                                  llmBound={true}
                                />
                              </div>
                              <Input
                                type="number"
                                value={category.scale?.min || 0}
                                onChange={(e) => updateCategory(index, 'scale', { ...category.scale, min: parseFloat(e.target.value) || 0 })}
                              />
                            </div>
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <Label>Scale Max</Label>
                                <InfoTooltip 
                                  content="Maximum score value for this category (typically 5). Defines the scoring range sent to the LLM. The LLM will score each category within this range."
                                  llmBound={true}
                                />
                              </div>
                              <Input
                                type="number"
                                value={category.scale?.max || 5}
                                onChange={(e) => updateCategory(index, 'scale', { ...category.scale, max: parseFloat(e.target.value) || 5 })}
                              />
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <Label>Description / Guidance</Label>
                              <InfoTooltip 
                                content="Detailed guidance explaining what this category evaluates and how to score it. This is sent directly to the LLM in the system prompt as 'guidance' to help the model understand how to evaluate documents against this category."
                                llmBound={true}
                              />
                            </div>
                            <Textarea
                              value={category.description}
                              onChange={(e) => updateCategory(index, 'description', e.target.value)}
                              placeholder="Describe what this category evaluates..."
                              rows={2}
                            />
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <Label>Criteria / Subcriteria</Label>
                                <InfoTooltip 
                                  content="Specific evaluation criteria or subcriteria for this category. These are sent to the LLM as 'subcriteria' to provide concrete evaluation points. The LLM uses these to assess documents more systematically."
                                  llmBound={true}
                                />
                              </div>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => addCriterion(index)}
                              >
                                <Plus className="h-4 w-4 mr-2" />
                                Add Criterion
                              </Button>
                            </div>
                            {category.criteria && category.criteria.length > 0 ? (
                              <div className="space-y-2">
                                {category.criteria.map((criterion, critIndex) => (
                                  <div key={critIndex} className="flex items-center space-x-2">
                                    <Input
                                      value={criterion}
                                      onChange={(e) => updateCriterion(index, critIndex, e.target.value)}
                                      placeholder="Enter criterion..."
                                    />
                                    <Button
                                      variant="destructive"
                                      size="sm"
                                      onClick={() => removeCriterion(index, critIndex)}
                                    >
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground">No criteria defined</p>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Thresholds */}
              <Card>
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <CardTitle>Score Thresholds</CardTitle>
                    <InfoTooltip 
                      content="Thresholds define the score ranges for automatic classification. These are sent to the LLM in the system prompt so it understands how to classify documents. After evaluation, the total weighted score is compared to these thresholds to assign Signal/Review/Noise labels."
                      llmBound={true}
                    />
                  </div>
                  <CardDescription>Minimum scores for Signal, Review, and Noise classifications</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Label htmlFor="signal_min">Signal Minimum</Label>
                        <InfoTooltip 
                          content="Minimum total weighted score (out of 5.0) required for a document to be classified as 'Signal' (high-value content). Documents scoring at or above this threshold are automatically promoted to the Library. Sent to LLM in system prompt."
                          llmBound={true}
                        />
                      </div>
                      <Input
                        id="signal_min"
                        type="number"
                        step="0.1"
                        value={formData.thresholds.signal_min}
                        onChange={(e) => setFormData({
                          ...formData,
                          thresholds: { ...formData.thresholds, signal_min: parseFloat(e.target.value) || 0 }
                        })}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Label htmlFor="review_min">Review Minimum</Label>
                        <InfoTooltip 
                          content="Minimum total weighted score required for 'Review' classification (requires human review). Documents scoring between review_min and signal_min need human evaluation. Sent to LLM in system prompt."
                          llmBound={true}
                        />
                      </div>
                      <Input
                        id="review_min"
                        type="number"
                        step="0.1"
                        value={formData.thresholds.review_min}
                        onChange={(e) => setFormData({
                          ...formData,
                          thresholds: { ...formData.thresholds, review_min: parseFloat(e.target.value) || 0 }
                        })}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Label htmlFor="noise_max">Noise Maximum</Label>
                        <InfoTooltip 
                          content="Maximum score for 'Noise' classification (low-value or irrelevant content). Documents scoring at or below this threshold are classified as Noise. Sent to LLM in system prompt."
                          llmBound={true}
                        />
                      </div>
                      <Input
                        id="noise_max"
                        type="number"
                        step="0.1"
                        value={formData.thresholds.noise_max}
                        onChange={(e) => setFormData({
                          ...formData,
                          thresholds: { ...formData.thresholds, noise_max: parseFloat(e.target.value) || 0 }
                        })}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Prompts */}
              <Card>
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <CardTitle>LLM Prompt References</CardTitle>
                    <InfoTooltip 
                      content="References to prompt templates used in different evaluation stages. These are identifiers that point to prompt templates stored elsewhere. The actual prompt content is not stored in the rubric - only references. Used by the evaluation service to load the appropriate prompts."
                      llmBound={true}
                    />
                  </div>
                  <CardDescription>References to LLM prompts for different evaluation stages</CardDescription>
                </CardHeader>
                <CardContent>
                  {loadingTemplates ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground mr-2" />
                      <span className="text-sm text-muted-foreground">Loading prompt templates...</span>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <Label htmlFor="prompt_metadata">Metadata Prompt</Label>
                          <InfoTooltip 
                            content="Reference ID for the prompt template used during metadata extraction. This prompt guides the LLM to extract structured metadata (title, authors, organization, publication date, etc.) from documents."
                            llmBound={true}
                          />
                        </div>
                        <Select
                          value={formData.prompts.metadata}
                          onValueChange={(value) => setFormData({
                            ...formData,
                            prompts: { ...formData.prompts, metadata: value }
                          })}
                        >
                          <SelectTrigger id="prompt_metadata">
                            <SelectValue placeholder="Select metadata template" />
                          </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          {promptTemplates
                            .filter(t => t.type === 'metadata' && t.is_active)
                            .map(template => (
                              <SelectItem key={template.id} value={template.reference_id}>
                                {template.name} {template.is_default && '(Default)'}
                              </SelectItem>
                            ))}
                        </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <Label htmlFor="prompt_evaluation">Evaluation Prompt</Label>
                          <InfoTooltip 
                            content="Reference ID for the main evaluation prompt template. This prompt, combined with the rubric categories and thresholds, guides the LLM to score documents across all categories and provide an overall classification."
                            llmBound={true}
                          />
                        </div>
                        <Select
                          value={formData.prompts.evaluation}
                          onValueChange={(value) => setFormData({
                            ...formData,
                            prompts: { ...formData.prompts, evaluation: value }
                          })}
                        >
                          <SelectTrigger id="prompt_evaluation">
                            <SelectValue placeholder="Select evaluation template" />
                          </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          {promptTemplates
                            .filter(t => t.type === 'evaluation' && t.is_active)
                            .map(template => (
                              <SelectItem key={template.id} value={template.reference_id}>
                                {template.name} {template.is_default && '(Default)'}
                              </SelectItem>
                            ))}
                        </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <Label htmlFor="prompt_clarification">Clarification Prompt</Label>
                          <InfoTooltip 
                            content="Reference ID for the clarification prompt template. This prompt guides the LLM to generate targeted web queries to gather additional context about authors, organizations, citations, and credibility signals."
                            llmBound={true}
                          />
                        </div>
                        <Select
                          value={formData.prompts.clarification}
                          onValueChange={(value) => setFormData({
                            ...formData,
                            prompts: { ...formData.prompts, clarification: value }
                          })}
                        >
                          <SelectTrigger id="prompt_clarification">
                            <SelectValue placeholder="Select clarification template" />
                          </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          {promptTemplates
                            .filter(t => t.type === 'clarification' && t.is_active)
                            .map(template => (
                              <SelectItem key={template.id} value={template.reference_id}>
                                {template.name} {template.is_default && '(Default)'}
                              </SelectItem>
                            ))}
                        </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving || loading}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                {isEditMode ? 'Updating...' : 'Creating...'}
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                {isEditMode ? 'Update Rubric' : 'Create Rubric'}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default RubricFormModal

