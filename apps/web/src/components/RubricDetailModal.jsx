import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { 
  Target, 
  Info, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  FileText
} from 'lucide-react'
import { API_URL } from '@/config.js'
import InfoTooltip from './InfoTooltip.jsx'
import { Button } from '@/components/ui/button.jsx'

const RubricDetailModal = ({ rubricId, open, onOpenChange, onViewNarrative }) => {
  const [rubric, setRubric] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (open && rubricId) {
      fetchRubricDetails()
    } else {
      setRubric(null)
      setError(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, rubricId])

  const fetchRubricDetails = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_URL}/api/v1/rubrics/${rubricId}`)
      if (!response.ok) throw new Error('Failed to fetch rubric details')
      const data = await response.json()
      setRubric(data)
    } catch (err) {
      console.error('Error fetching rubric details:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatCategoryName = (key) => {
    return key.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const getCategoryWeight = (category) => {
    return Math.round((category.weight || 0) * 100)
  }

  const formatSubcriteria = (subcriteria) => {
    if (!subcriteria || !Array.isArray(subcriteria)) return []
    return subcriteria.map(sc => 
      sc.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    )
  }

  if (!open) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[2400px] max-h-[90vh]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <DialogTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5" />
                <span>Rubric Details</span>
                {rubric?.is_active && (
                  <Badge variant="default" className="bg-green-500">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                )}
              </DialogTitle>
              <DialogDescription>
                {rubric ? `Version ${rubric.version} • Created ${new Date(rubric.created_at).toLocaleDateString()}` : 'Loading rubric details...'}
              </DialogDescription>
            </div>
            {rubric && onViewNarrative && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onViewNarrative(rubricId)}
                className="ml-4"
              >
                <FileText className="h-4 w-4 mr-2" />
                View LLM Narrative
              </Button>
            )}
          </div>
        </DialogHeader>

        <ScrollArea className="max-h-[calc(90vh-200px)] pr-4">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="flex items-center space-x-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                <span>Error loading rubric: {error}</span>
              </div>
            </div>
          )}

          {rubric && !loading && (
            <div className="space-y-6">
              {/* Rubric Overview */}
              <Card>
                <CardHeader>
                  <CardTitle>Rubric Overview</CardTitle>
                  <CardDescription>Basic information about this evaluation rubric</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Version</div>
                      <div className="text-lg font-semibold">{rubric.version}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Status</div>
                      <div>
                        <Badge variant={rubric.is_active ? 'default' : 'secondary'}>
                          {rubric.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Created</div>
                      <div className="text-sm">{new Date(rubric.created_at).toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Categories</div>
                      <div className="text-sm">
                        {Array.isArray(rubric.categories) 
                          ? rubric.categories.length 
                          : Object.keys(rubric.categories || {}).length} categories
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Evaluation Categories */}
              {rubric.categories && (Array.isArray(rubric.categories) ? rubric.categories.length > 0 : Object.keys(rubric.categories).length > 0) && (
                <Card>
                  <CardHeader>
                    <CardTitle>Evaluation Categories</CardTitle>
                    <CardDescription>
                      Weighted scoring areas and their evaluation criteria
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {(Array.isArray(rubric.categories)
                        ? rubric.categories.map((cat, idx) => [cat.id || `category_${idx}`, cat])
                        : Object.entries(rubric.categories)
                      )
                        .sort(([, a], [, b]) => (b.weight || 0) - (a.weight || 0))
                        .map(([key, category]) => (
                          <div key={key} className="border rounded-lg p-4 space-y-3">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-2">
                                  <h4 className="font-semibold text-lg">
                                    {category.name || formatCategoryName(key)}
                                  </h4>
                                  <Badge variant="outline" className="font-mono">
                                    {getCategoryWeight(category)}%
                                  </Badge>
                                </div>
                                <p className="text-sm text-muted-foreground mb-3">
                                  {category.description || category.guidance || 'No guidance provided'}
                                </p>
                              </div>
                            </div>

                            {(category.criteria || category.subcriteria) && (category.criteria || category.subcriteria).length > 0 && (
                              <div>
                                <div className="text-xs font-medium text-muted-foreground mb-2">
                                  Criteria:
                                </div>
                                <div className="flex flex-wrap gap-2">
                                  {(category.criteria || category.subcriteria).map((criteria, idx) => (
                                    <Badge key={idx} variant="secondary" className="text-xs">
                                      {typeof criteria === 'string' ? criteria : criteria.toString()}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Score Thresholds */}
              {rubric.thresholds && (
                <Card>
                  <CardHeader>
                    <CardTitle>Score Thresholds</CardTitle>
                    <CardDescription>
                      Minimum scores required for Signal, Review, and Noise classifications
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                        <div className="text-xs font-medium text-muted-foreground mb-1">Signal</div>
                        <div className="text-2xl font-bold text-green-600">
                          ≥ {rubric.thresholds.signal_min || 'N/A'}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          High-value content
                        </div>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                        <div className="text-xs font-medium text-muted-foreground mb-1">Review</div>
                        <div className="text-2xl font-bold text-yellow-600">
                          ≥ {rubric.thresholds.review_min || 'N/A'}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Requires manual review
                        </div>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-gray-500/10 border border-gray-500/20">
                        <div className="text-xs font-medium text-muted-foreground mb-1">Noise</div>
                        <div className="text-2xl font-bold text-gray-600">
                          ≤ {rubric.thresholds.noise_max || rubric.thresholds.review_min || 'N/A'}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Low-value content
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Prompts */}
              {rubric.prompts && Object.keys(rubric.prompts).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>LLM Prompts</CardTitle>
                    <CardDescription>
                      Prompt references used for different evaluation stages
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(rubric.prompts).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                          <div>
                            <div className="font-medium text-sm">
                              {formatCategoryName(key)}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Prompt reference identifier
                            </div>
                          </div>
                          <Badge variant="outline" className="font-mono text-xs">
                            {value}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </ScrollArea>

        <DialogFooter>
          <button
            onClick={() => onOpenChange(false)}
            className="px-4 py-2 text-sm font-medium rounded-md border border-input bg-background hover:bg-accent"
          >
            Close
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default RubricDetailModal

