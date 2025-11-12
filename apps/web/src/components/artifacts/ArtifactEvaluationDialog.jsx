/**
 * ArtifactEvaluationDialog Component
 * Dialog for triggering artifact evaluation with rubric selection
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { PlayCircle, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'
import { API_URL } from '@/config.js'

const ArtifactEvaluationDialog = ({
  open,
  onOpenChange,
  evaluationTarget,
  evaluationReadiness,
  onEvaluate
}) => {
  const [rubrics, setRubrics] = useState([])
  const [selectedRubric, setSelectedRubric] = useState('')

  // Fetch rubrics when dialog opens
  useEffect(() => {
    if (open) {
      fetchRubrics()
    }
  }, [open])

  // Set default rubric when evaluation target changes
  useEffect(() => {
    if (evaluationTarget && evaluationReadiness[evaluationTarget.id]) {
      const defaultRubric = evaluationReadiness[evaluationTarget.id]?.rubric_version || ''
      setSelectedRubric(defaultRubric)
    }
  }, [evaluationTarget, evaluationReadiness])

  const fetchRubrics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/rubrics/?limit=100`)
      if (response.ok) {
        const data = await response.json()
        // Sort: active rubrics first, then by created date
        const sortedRubrics = (data.items || []).sort((a, b) => {
          if (a.is_active && !b.is_active) return -1
          if (!a.is_active && b.is_active) return 1
          return new Date(b.created_at) - new Date(a.created_at)
        })
        setRubrics(sortedRubrics)
      }
    } catch (err) {
      console.error('Error fetching rubrics:', err)
    }
  }

  const handleEvaluate = () => {
    if (!selectedRubric) {
      toast.error('Please select a rubric')
      return
    }
    onEvaluate(evaluationTarget, selectedRubric)
  }

  if (!evaluationTarget) return null

  const readiness = evaluationReadiness[evaluationTarget.id]
  const isReady = readiness?.ready === true

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 flex-shrink-0">
          <DialogTitle>Evaluate Artifact</DialogTitle>
          <DialogDescription>
            Select a rubric to use for evaluating this artifact. The evaluation will run in the background.
          </DialogDescription>
        </DialogHeader>
        
        <ScrollArea className="flex-1 min-h-0 px-6">
          <div className="space-y-4 py-4">
            <div>
              <Label className="text-sm font-medium">Artifact</Label>
              <p className="text-sm text-muted-foreground mt-1">{evaluationTarget.title}</p>
            </div>
            
            <div>
              <Label htmlFor="rubric-select" className="text-sm font-medium">
                Rubric
              </Label>
              <Select
                id="rubric-select"
                value={selectedRubric}
                onValueChange={setSelectedRubric}
              >
                <SelectTrigger className="mt-2">
                  <SelectValue placeholder="Select a rubric" />
                </SelectTrigger>
                <SelectContent>
                  {rubrics.length === 0 ? (
                    <SelectItem value="" disabled>No rubrics available</SelectItem>
                  ) : (
                    rubrics.map((rubric) => (
                      <SelectItem key={rubric.id} value={rubric.version}>
                        {rubric.version} {rubric.is_active && '(Active)'}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {readiness?.llm_provider_name && (
                <p className="text-xs text-muted-foreground mt-2">
                  Using LLM Provider: {readiness.llm_provider_name}
                </p>
              )}
            </div>
            
            {readiness?.reasons && readiness.reasons.length > 0 && (
              <div className="rounded-md bg-yellow-500/10 border border-yellow-500/20 p-3">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                      Evaluation Not Ready
                    </p>
                    <ul className="text-xs text-yellow-700 dark:text-yellow-400 mt-1 list-disc list-inside">
                      {readiness.reasons.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
        
        <DialogFooter className="px-6 pb-6 pt-4 flex-shrink-0 border-t">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleEvaluate}
            disabled={!isReady || !selectedRubric}
          >
            <PlayCircle className="h-4 w-4 mr-2" />
            Start Evaluation
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ArtifactEvaluationDialog

