import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import {
  FileText,
  Plus,
  Edit,
  Trash2,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Copy,
  Check,
  Play,
  GitCompare
} from 'lucide-react'
import { API_URL } from '@/config.js'
import { toast } from 'sonner'
import InfoTooltip from './InfoTooltip.jsx'

const PromptTemplates = () => {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [showDialog, setShowDialog] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState(null)
  const [formData, setFormData] = useState({
    reference_id: '',
    name: '',
    type: 'metadata',
    version: '',
    system_prompt: '',
    user_prompt_template: '',
    description: '',
    is_active: true,
    is_default: false,
    tags: []
  })
  const [copiedField, setCopiedField] = useState(null)
  const [showTestDialog, setShowTestDialog] = useState(false)
  const [testingTemplate, setTestingTemplate] = useState(null)
  const [testVariables, setTestVariables] = useState({})
  const [renderedPrompt, setRenderedPrompt] = useState('')
  const [showCompareDialog, setShowCompareDialog] = useState(false)
  const [comparingTemplates, setComparingTemplates] = useState({ left: null, right: null })

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/api/v1/prompt-templates/`)
      if (response.ok) {
        const data = await response.json()
        setTemplates(data.items || [])
      } else {
        toast.error('Failed to load prompt templates')
        setTemplates([])
      }
    } catch (error) {
      console.error('Error fetching templates:', error)
      toast.error(`Error loading templates: ${error.message}`)
      setTemplates([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddTemplate = () => {
    setEditingTemplate(null)
    setFormData({
      reference_id: '',
      name: '',
      type: 'metadata',
      version: '',
      system_prompt: '',
      user_prompt_template: '',
      description: '',
      is_active: true,
      is_default: false,
      tags: []
    })
    setShowDialog(true)
  }

  const handleEditTemplate = async (template) => {
    // Fetch full template details to get system_prompt and user_prompt_template
    try {
      const response = await fetch(`${API_URL}/api/v1/prompt-templates/${template.id}`)
      if (response.ok) {
        const fullTemplate = await response.json()
        setEditingTemplate(fullTemplate)
        setFormData({
          reference_id: fullTemplate.reference_id,
          name: fullTemplate.name,
          type: fullTemplate.type,
          version: fullTemplate.version,
          system_prompt: fullTemplate.system_prompt || '',
          user_prompt_template: fullTemplate.user_prompt_template || '',
          description: fullTemplate.description || '',
          is_active: fullTemplate.is_active,
          is_default: fullTemplate.is_default,
          tags: fullTemplate.tags || []
        })
        setShowDialog(true)
      } else {
        toast.error('Failed to load template details')
      }
    } catch (error) {
      console.error('Error fetching template details:', error)
      toast.error(`Error loading template: ${error.message}`)
    }
  }

  const handleSaveTemplate = async () => {
    try {
      if (!formData.reference_id || !formData.name || !formData.user_prompt_template) {
        toast.error('Please fill in all required fields')
        return
      }

      const url = editingTemplate
        ? `${API_URL}/api/v1/prompt-templates/${editingTemplate.id}`
        : `${API_URL}/api/v1/prompt-templates/`
      
      const method = editingTemplate ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        toast.success(`Prompt template ${editingTemplate ? 'updated' : 'created'} successfully`)
        setShowDialog(false)
        fetchTemplates()
      } else {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        toast.error(error.detail || 'Failed to save template')
      }
    } catch (error) {
      console.error('Error saving template:', error)
      toast.error(`Error saving template: ${error.message}`)
    }
  }

  const handleDeleteTemplate = async (templateId) => {
    if (!confirm('Are you sure you want to delete this prompt template?')) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/api/v1/prompt-templates/${templateId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        toast.success('Prompt template deleted successfully')
        fetchTemplates()
      } else {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        toast.error(error.detail || 'Failed to delete template')
      }
    } catch (error) {
      console.error('Error deleting template:', error)
      toast.error(`Error deleting template: ${error.message}`)
    }
  }

  const handleCopy = async (text, field) => {
    if (!text) {
      toast.error('Nothing to copy')
      return
    }

    try {
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text)
        setCopiedField(field)
        setTimeout(() => setCopiedField(null), 2000)
        toast.success('Copied to clipboard')
        return
      }

      // Fallback for older browsers or non-secure contexts
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      try {
        const successful = document.execCommand('copy')
        if (successful) {
          setCopiedField(field)
          setTimeout(() => setCopiedField(null), 2000)
          toast.success('Copied to clipboard')
        } else {
          throw new Error('execCommand failed')
        }
      } finally {
        document.body.removeChild(textArea)
      }
    } catch (error) {
      console.error('Copy failed:', error)
      toast.error(`Failed to copy: ${error.message || 'Clipboard access denied'}`)
    }
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'metadata': return 'bg-blue-500'
      case 'evaluation': return 'bg-green-500'
      case 'clarification': return 'bg-purple-500'
      default: return 'bg-gray-500'
    }
  }

  const handleTestTemplate = async (template) => {
    // Fetch full template details to get user_prompt_template with variables
    try {
      const response = await fetch(`${API_URL}/api/v1/prompt-templates/${template.id}`)
      if (!response.ok) {
        toast.error('Failed to load template details for testing')
        return
      }
      const fullTemplate = await response.json()
      setTestingTemplate(fullTemplate)
      
      // Initialize test variables with defaults based on template type
      const defaultVars = {}
      
      // Extract variables from the user_prompt_template using regex
      const variableRegex = /\{(\w+)\}/g
      const matches = fullTemplate.user_prompt_template.matchAll(variableRegex)
      const variables = Array.from(new Set(Array.from(matches, m => m[1])))
      
      // Set default sample values based on variable names
      variables.forEach(key => {
        if (key.includes('uri') || key.includes('url')) {
          defaultVars[key] = 'https://example.com/document.pdf'
        } else if (key.includes('title')) {
          defaultVars[key] = 'Sample Document Title'
        } else if (key.includes('authors')) {
          defaultVars[key] = 'John Doe, Jane Smith'
        } else if (key.includes('organization')) {
          defaultVars[key] = 'Sample Organization'
        } else if (key.includes('date')) {
          defaultVars[key] = '2024-01-15'
        } else if (key.includes('topics')) {
          defaultVars[key] = 'Military Strategy, Geopolitics'
        } else if (key.includes('language')) {
          defaultVars[key] = 'en'
        } else if (key.includes('content') || key.includes('preview')) {
          defaultVars[key] = 'This is a sample document content. It contains some text that would typically be found in a real document. ' +
            'The content includes multiple sentences and paragraphs to demonstrate how the prompt template would handle longer text.'
        } else if (key.includes('categories') || key.includes('rubric')) {
          defaultVars[key] = JSON.stringify({
            credibility: { weight: 0.25, guidance: 'Sample guidance' },
            relevance: { weight: 0.20, guidance: 'Sample guidance' }
          }, null, 2)
        } else if (key.includes('signals')) {
          defaultVars[key] = '[]'
        } else if (key.includes('min') || key.includes('max')) {
          defaultVars[key] = '3.5'
        } else {
          defaultVars[key] = `Sample ${key}`
        }
      })
      
      setTestVariables(defaultVars)
      setRenderedPrompt('')
      setShowTestDialog(true)
    } catch (error) {
      console.error('Error fetching template details:', error)
      toast.error(`Error loading template: ${error.message}`)
    }
  }

  const renderPrompt = () => {
    if (!testingTemplate) return
    
    try {
      // Extract variables from template using regex
      const variableRegex = /\{(\w+)\}/g
      const matches = testingTemplate.user_prompt_template.matchAll(variableRegex)
      const variables = Array.from(matches, m => m[1])
      
      // Build substitution object
      const substitutions = {}
      variables.forEach(varName => {
        substitutions[varName] = testVariables[varName] || `{${varName}}`
      })
      
      // Render the prompt
      let rendered = testingTemplate.user_prompt_template
      Object.keys(substitutions).forEach(key => {
        const regex = new RegExp(`\\{${key}\\}`, 'g')
        rendered = rendered.replace(regex, substitutions[key])
      })
      
      setRenderedPrompt(rendered)
    } catch (error) {
      console.error('Error rendering prompt:', error)
      toast.error('Error rendering prompt template')
    }
  }

  useEffect(() => {
    if (showTestDialog && testingTemplate) {
      renderPrompt()
    }
  }, [testVariables, testingTemplate, showTestDialog])

  const handleCompareTemplates = (template) => {
    // Find other templates of the same type
    const sameTypeTemplates = templates.filter(t => 
      t.type === template.type && t.id !== template.id
    )
    
    if (sameTypeTemplates.length === 0) {
      toast.info('No other templates of the same type to compare')
      return
    }
    
    setComparingTemplates({
      left: template,
      right: sameTypeTemplates[0] // Default to first other template
    })
    setShowCompareDialog(true)
  }

  const getTemplateVersions = (type) => {
    return templates.filter(t => t.type === type).sort((a, b) => {
      // Sort by version (simple string comparison, could be improved)
      return a.version.localeCompare(b.version)
    })
  }

  const filteredTemplates = templates

  return (
    <div className="space-y-6">
      <Card className="aulendur-gradient-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Prompt Templates</span>
              </CardTitle>
              <CardDescription>Manage LLM prompt templates for metadata extraction, evaluation, and clarification</CardDescription>
            </div>
            <Button onClick={handleAddTemplate} size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Template
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">Loading templates...</span>
            </div>
          ) : filteredTemplates.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">No prompt templates configured</p>
              <Button onClick={handleAddTemplate} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Template
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredTemplates.map((template) => (
                <Card 
                  key={template.id} 
                  className={`aulendur-hover-transform ${
                    template.is_default 
                      ? 'border-2 border-primary shadow-lg bg-primary/5 dark:bg-primary/10' 
                      : ''
                  }`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2 flex-wrap gap-2">
                          <span className="font-medium">{template.name}</span>
                          <Badge className={getTypeColor(template.type)}>
                            {template.type}
                          </Badge>
                          {template.is_default && (
                            <Badge variant="default" className="font-semibold">Default</Badge>
                          )}
                          {template.is_active ? (
                            <Badge variant="default" className="bg-green-500">Active</Badge>
                          ) : (
                            <Badge variant="secondary">Inactive</Badge>
                          )}
                          <Badge variant="outline">v{template.version}</Badge>
                        </div>
                        <div className="text-sm text-muted-foreground mb-2">
                          Reference ID: <code className="text-xs bg-muted px-1 py-0.5 rounded">{template.reference_id}</code>
                        </div>
                        {template.description && (
                          <p className="text-sm text-muted-foreground mb-2">{template.description}</p>
                        )}
                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                          <span>Used {template.usage_count || 0} times</span>
                          <span>•</span>
                          <span>Created {new Date(template.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleTestTemplate(template)}
                          title="Test Template"
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                        {templates.filter(t => t.type === template.type && t.id !== template.id).length > 0 && (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleCompareTemplates(template)}
                            title="Compare Versions"
                          >
                            <GitCompare className="h-4 w-4" />
                          </Button>
                        )}
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleEditTemplate(template)}
                          title="Edit Template"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        {!template.is_default && (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleDeleteTemplate(template.id)}
                            className="text-red-500 hover:text-red-700"
                            title="Delete Template"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Template Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col p-0 overflow-hidden">
          <DialogHeader className="px-6 pt-6 pb-4 flex-shrink-0">
            <DialogTitle>
              {editingTemplate ? 'Edit Prompt Template' : 'Add Prompt Template'}
            </DialogTitle>
            <DialogDescription>
              Configure a prompt template for LLM interactions
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="flex-1 min-h-0 px-6">
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Label htmlFor="reference_id">Reference ID *</Label>
                    <InfoTooltip 
                      content="Unique identifier starting with 'prompt_ref_' (e.g., 'prompt_ref_meta_v2_1'). Used to reference this template in rubrics."
                      llmBound={true}
                    />
                  </div>
                  <Input
                    id="reference_id"
                    value={formData.reference_id}
                    onChange={(e) => setFormData({ ...formData, reference_id: e.target.value })}
                    placeholder="prompt_ref_meta_v2_1"
                    disabled={!!editingTemplate}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Metadata Extraction v2.1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="type">Type *</Label>
                  <Select
                    value={formData.type}
                    onValueChange={(value) => setFormData({ ...formData, type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="metadata">Metadata</SelectItem>
                      <SelectItem value="evaluation">Evaluation</SelectItem>
                      <SelectItem value="clarification">Clarification</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="version">Version *</Label>
                  <Input
                    id="version"
                    value={formData.version}
                    onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                    placeholder="v2.1"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief description of what this prompt does..."
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Label htmlFor="system_prompt">System Prompt</Label>
                    <InfoTooltip 
                      content="System prompt that establishes the LLM's role and context. Optional for some prompt types."
                      llmBound={true}
                    />
                  </div>
                  {formData.system_prompt && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(formData.system_prompt, 'system')}
                    >
                      {copiedField === 'system' ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  )}
                </div>
                <Textarea
                  id="system_prompt"
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  placeholder="You are an expert..."
                  rows={6}
                  className="font-mono text-sm"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Label htmlFor="user_prompt_template">User Prompt Template *</Label>
                    <InfoTooltip 
                      content="Template for the user prompt with placeholders like {variable_name}. Use curly braces for variables that will be substituted at runtime."
                      llmBound={true}
                    />
                  </div>
                  {formData.user_prompt_template && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(formData.user_prompt_template, 'user')}
                    >
                      {copiedField === 'user' ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  )}
                </div>
                <Textarea
                  id="user_prompt_template"
                  value={formData.user_prompt_template}
                  onChange={(e) => setFormData({ ...formData, user_prompt_template: e.target.value })}
                  placeholder="Extract metadata from: {document_content}..."
                  rows={10}
                  className="font-mono text-sm"
                />
              </div>

              <div className="flex items-center space-x-6">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4"
                  />
                  <span className="text-sm font-medium">Active</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                    className="h-4 w-4"
                  />
                  <span className="text-sm font-medium">Set as default for this type</span>
                </label>
              </div>
            </div>
          </ScrollArea>
          <DialogFooter className="px-6 pb-6 pt-4 flex-shrink-0 border-t">
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveTemplate}>
              {editingTemplate ? 'Save Changes' : 'Create Template'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Test Template Dialog */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent className="max-w-5xl max-h-[90vh] flex flex-col p-0 overflow-hidden">
          <DialogHeader className="px-6 pt-6 pb-4 flex-shrink-0">
            <DialogTitle>Test Prompt Template: {testingTemplate?.name}</DialogTitle>
            <DialogDescription>
              Enter sample data to preview how the prompt will be rendered
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="flex-1 min-h-0 px-6">
            <div className="space-y-6 py-4">
              {testingTemplate && (
                <>
                  {/* Template Info */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Template Details</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div><strong>Type:</strong> {testingTemplate.type}</div>
                      <div><strong>Version:</strong> {testingTemplate.version}</div>
                      <div><strong>Reference ID:</strong> <code className="text-xs bg-muted px-1 py-0.5 rounded">{testingTemplate.reference_id}</code></div>
                    </CardContent>
                  </Card>

                  {/* System Prompt Preview */}
                  {testingTemplate.system_prompt && (
                    <div className="space-y-2">
                      <Label>System Prompt</Label>
                      <div className="p-3 bg-muted rounded-md font-mono text-sm max-h-40 overflow-auto">
                        {testingTemplate.system_prompt}
                      </div>
                    </div>
                  )}

                  {/* Variable Inputs */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label>Template Variables</Label>
                      <Button variant="outline" size="sm" onClick={renderPrompt}>
                        Refresh Preview
                      </Button>
                    </div>
                    {(() => {
                      // Extract variables from template
                      const variableRegex = /\{(\w+)\}/g
                      const matches = testingTemplate.user_prompt_template.matchAll(variableRegex)
                      const variables = Array.from(new Set(Array.from(matches, m => m[1])))
                      
                      if (variables.length === 0) {
                        return <p className="text-sm text-muted-foreground">No variables found in template</p>
                      }
                      
                      return (
                        <div className="space-y-3">
                          {variables.map(varName => (
                            <div key={varName} className="space-y-1">
                              <Label htmlFor={`var_${varName}`} className="text-sm">
                                {varName}
                              </Label>
                              <Textarea
                                id={`var_${varName}`}
                                value={testVariables[varName] || ''}
                                onChange={(e) => setTestVariables({
                                  ...testVariables,
                                  [varName]: e.target.value
                                })}
                                placeholder={`Enter value for {${varName}}`}
                                rows={varName.includes('content') || varName.includes('preview') || varName.includes('categories') ? 4 : 2}
                                className="font-mono text-sm"
                              />
                            </div>
                          ))}
                        </div>
                      )
                    })()}
                  </div>

                  {/* Rendered Prompt Preview */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Rendered Prompt Preview</Label>
                      {renderedPrompt && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopy(renderedPrompt, 'rendered')}
                        >
                          {copiedField === 'rendered' ? (
                            <Check className="h-4 w-4 mr-2" />
                          ) : (
                            <Copy className="h-4 w-4 mr-2" />
                          )}
                          Copy
                        </Button>
                      )}
                    </div>
                    <div className="p-4 bg-muted rounded-md font-mono text-sm whitespace-pre-wrap max-h-96 overflow-auto">
                      {renderedPrompt || 'Enter values above and click "Refresh Preview" to see rendered prompt'}
                    </div>
                  </div>
                </>
              )}
            </div>
          </ScrollArea>
          <DialogFooter className="px-6 pb-6 pt-4 flex-shrink-0 border-t">
            <Button variant="outline" onClick={() => setShowTestDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Compare Templates Dialog */}
      <Dialog open={showCompareDialog} onOpenChange={setShowCompareDialog}>
        <DialogContent className="max-w-7xl max-h-[90vh] flex flex-col p-0 overflow-hidden">
          <DialogHeader className="px-6 pt-6 pb-4 flex-shrink-0">
            <DialogTitle>Compare Template Versions</DialogTitle>
            <DialogDescription>
              Compare different versions of {comparingTemplates.left?.type} templates side-by-side
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="flex-1 pr-4 min-h-0">
            <div className="space-y-6 py-4">
              {comparingTemplates.left && (
                <>
                  {/* Template Selectors */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Left Template</Label>
                      <Select
                        value={comparingTemplates.left.id}
                        onValueChange={(value) => {
                          const template = templates.find(t => t.id === value)
                          if (template) setComparingTemplates({ ...comparingTemplates, left: template })
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {getTemplateVersions(comparingTemplates.left.type).map(t => (
                            <SelectItem key={t.id} value={t.id}>
                              {t.name} (v{t.version}) {t.is_default && '(Default)'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Right Template</Label>
                      <Select
                        value={comparingTemplates.right?.id || ''}
                        onValueChange={(value) => {
                          const template = templates.find(t => t.id === value)
                          if (template) setComparingTemplates({ ...comparingTemplates, right: template })
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select template to compare" />
                        </SelectTrigger>
                        <SelectContent>
                          {getTemplateVersions(comparingTemplates.left.type)
                            .filter(t => t.id !== comparingTemplates.left.id)
                            .map(t => (
                              <SelectItem key={t.id} value={t.id}>
                                {t.name} (v{t.version}) {t.is_default && '(Default)'}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Comparison View */}
                  {comparingTemplates.right && (
                    <div className="grid grid-cols-2 gap-4">
                      {/* Left Template */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-sm flex items-center justify-between">
                            <span>{comparingTemplates.left.name}</span>
                            {comparingTemplates.left.is_default && (
                              <Badge variant="default">Default</Badge>
                            )}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Version {comparingTemplates.left.version} • Reference: {comparingTemplates.left.reference_id}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {comparingTemplates.left.system_prompt && (
                            <div className="space-y-2">
                              <Label className="text-xs">System Prompt</Label>
                              <div className="p-3 bg-muted rounded-md font-mono text-xs max-h-32 overflow-auto">
                                {comparingTemplates.left.system_prompt}
                              </div>
                            </div>
                          )}
                          <div className="space-y-2">
                            <Label className="text-xs">User Prompt Template</Label>
                            <div className="p-3 bg-muted rounded-md font-mono text-xs max-h-64 overflow-auto whitespace-pre-wrap">
                              {comparingTemplates.left.user_prompt_template}
                            </div>
                          </div>
                          {comparingTemplates.left.description && (
                            <div className="space-y-2">
                              <Label className="text-xs">Description</Label>
                              <p className="text-sm text-muted-foreground">{comparingTemplates.left.description}</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>

                      {/* Right Template */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-sm flex items-center justify-between">
                            <span>{comparingTemplates.right.name}</span>
                            {comparingTemplates.right.is_default && (
                              <Badge variant="default">Default</Badge>
                            )}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Version {comparingTemplates.right.version} • Reference: {comparingTemplates.right.reference_id}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {comparingTemplates.right.system_prompt && (
                            <div className="space-y-2">
                              <Label className="text-xs">System Prompt</Label>
                              <div className="p-3 bg-muted rounded-md font-mono text-xs max-h-32 overflow-auto">
                                {comparingTemplates.right.system_prompt}
                              </div>
                            </div>
                          )}
                          <div className="space-y-2">
                            <Label className="text-xs">User Prompt Template</Label>
                            <div className="p-3 bg-muted rounded-md font-mono text-xs max-h-64 overflow-auto whitespace-pre-wrap">
                              {comparingTemplates.right.user_prompt_template}
                            </div>
                          </div>
                          {comparingTemplates.right.description && (
                            <div className="space-y-2">
                              <Label className="text-xs">Description</Label>
                              <p className="text-sm text-muted-foreground">{comparingTemplates.right.description}</p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  )}
                </>
              )}
            </div>
          </ScrollArea>
          <DialogFooter className="px-6 pb-6 pt-4 flex-shrink-0 border-t">
            <Button variant="outline" onClick={() => setShowCompareDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default PromptTemplates

