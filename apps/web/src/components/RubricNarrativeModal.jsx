import { useState, useEffect } from 'react'
import { API_URL } from '@/config.js'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import {
  FileText,
  Loader2,
  AlertCircle,
  Copy,
  CheckCircle
} from 'lucide-react'

const RubricNarrativeModal = ({ rubricId, open, onOpenChange }) => {
  const [rubric, setRubric] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (open && rubricId) {
      fetchRubric()
    } else {
      setRubric(null)
      setError(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, rubricId])

  const fetchRubric = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_URL}/api/v1/rubrics/${rubricId}`)
      if (!response.ok) throw new Error('Failed to fetch rubric')
      const data = await response.json()
      setRubric(data)
    } catch (err) {
      console.error('Error fetching rubric:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const buildSystemPrompt = () => {
    if (!rubric) return ''

    // Convert categories to the format expected by the LLM
    const categories = Array.isArray(rubric.categories)
      ? rubric.categories.reduce((acc, cat) => {
          acc[cat.id] = {
            weight: cat.weight,
            guidance: cat.description || cat.guidance || '',
            subcriteria: cat.criteria || cat.subcriteria || [],
            scale: cat.scale || { min: 0, max: 5 }
          }
          return acc
        }, {})
      : rubric.categories

    return `You are an expert evaluator for military wargaming research documents.
Your task is to evaluate documents against specific criteria and provide structured scores.

Rubric Version: ${rubric.version}

Categories and Weights:
${JSON.stringify(categories, null, 2)}

Thresholds:
- Signal: >= ${rubric.thresholds?.signal_min || 3.8}
- Review: >= ${rubric.thresholds?.review_min || 2.8}
- Noise: < ${rubric.thresholds?.review_min || 2.8}

Score each category from 0-5 based on the guidance provided.
Provide an overall label (Signal/Review/Noise) and confidence score (0.0-1.0).`
  }

  const buildEvaluationPrompt = (sampleMetadata = {}) => {
    if (!rubric) return ''

    return `Evaluate the following document:

URI: ${sampleMetadata.uri || '[Document URI]'}
Title: ${sampleMetadata.title || 'Unknown'}
Authors: ${sampleMetadata.authors?.join(', ') || 'Unknown'}
Organization: ${sampleMetadata.organization || 'Unknown'}
Publication Date: ${sampleMetadata.publication_date || 'Unknown'}

Content:
[Document content preview - first 5000 characters]

Evaluate against the rubric categories and provide structured scores.`
  }

  const fullNarrative = () => {
    if (!rubric) return ''
    
    const systemPrompt = buildSystemPrompt()
    const evaluationPrompt = buildEvaluationPrompt()
    
    return `=== SYSTEM PROMPT ===

${systemPrompt}

=== USER PROMPT (Evaluation) ===

${evaluationPrompt}

=== PROMPT REFERENCES ===

Metadata Prompt: ${rubric.prompts?.metadata || 'Not specified'}
Evaluation Prompt: ${rubric.prompts?.evaluation || 'Not specified'}
Clarification Prompt: ${rubric.prompts?.clarification || 'Not specified'}`
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(fullNarrative())
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  if (!open) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[2400px] max-h-[90vh] flex flex-col p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 flex-shrink-0">
          <DialogTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>LLM Prompt Narrative</span>
          </DialogTitle>
          <DialogDescription>
            View how this rubric is formatted as prompts sent to the LLM during evaluation
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 min-h-0 px-6">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 mb-4">
              <div className="flex items-center space-x-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                <span>Error loading rubric: {error}</span>
              </div>
            </div>
          )}

          {rubric && !loading && (
            <div className="space-y-6">
              {/* Info Card */}
              <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
                <CardHeader>
                  <CardTitle className="text-blue-900 dark:text-blue-100">About This View</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    This narrative shows exactly how your rubric is formatted and sent to the LLM during evaluation.
                    The system prompt contains your rubric version, categories, weights, guidance, and thresholds.
                    The user prompt contains the document metadata and content. Use this view to understand how
                    the LLM interprets your rubric configuration.
                  </p>
                </CardContent>
              </Card>

              {/* Full Narrative - Moved to top */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Complete Prompt Narrative</CardTitle>
                      <CardDescription>
                        Full formatted prompt as it appears to the LLM (includes system and user prompts)
                      </CardDescription>
                    </div>
                    <Button onClick={handleCopy} variant="outline" size="sm">
                      {copied ? (
                        <>
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy Full Narrative
                        </>
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted p-4 rounded-lg font-mono text-xs whitespace-pre-wrap max-h-96 overflow-auto">
                    {fullNarrative()}
                  </div>
                </CardContent>
              </Card>

              {/* System Prompt */}
              <Card>
                <CardHeader>
                  <CardTitle>System Prompt</CardTitle>
                  <CardDescription>
                    This prompt is sent to the LLM to establish its role and provide evaluation criteria
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted p-4 rounded-lg font-mono text-sm whitespace-pre-wrap">
                    {buildSystemPrompt()}
                  </div>
                </CardContent>
              </Card>

              {/* User Prompt */}
              <Card>
                <CardHeader>
                  <CardTitle>User Prompt (Evaluation)</CardTitle>
                  <CardDescription>
                    This prompt contains the document information sent to the LLM for evaluation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted p-4 rounded-lg font-mono text-sm whitespace-pre-wrap">
                    {buildEvaluationPrompt()}
                  </div>
                </CardContent>
              </Card>

              {/* Prompt References */}
              {rubric.prompts && Object.keys(rubric.prompts).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Prompt Template References</CardTitle>
                    <CardDescription>
                      References to prompt templates used in different evaluation stages
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {rubric.prompts.metadata && (
                        <div className="flex items-center justify-between p-2 rounded bg-muted/50">
                          <span className="font-medium">Metadata Prompt:</span>
                          <Badge variant="secondary">{rubric.prompts.metadata}</Badge>
                        </div>
                      )}
                      {rubric.prompts.evaluation && (
                        <div className="flex items-center justify-between p-2 rounded bg-muted/50">
                          <span className="font-medium">Evaluation Prompt:</span>
                          <Badge variant="secondary">{rubric.prompts.evaluation}</Badge>
                        </div>
                      )}
                      {rubric.prompts.clarification && (
                        <div className="flex items-center justify-between p-2 rounded bg-muted/50">
                          <span className="font-medium">Clarification Prompt:</span>
                          <Badge variant="secondary">{rubric.prompts.clarification}</Badge>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </ScrollArea>
        <DialogFooter className="px-6 pb-6 pt-4 flex-shrink-0 border-t">
          <Button onClick={() => onOpenChange(false)}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default RubricNarrativeModal

