/**
 * ArtifactCard Component
 * Individual artifact card displayed in the sidebar list
 * Handles selection, expansion, evaluation status, and actions
 */

import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible.jsx'
import { 
  Clock, 
  Loader2,
  ChevronDown,
  ChevronUp,
  PlayCircle,
  Trash2
} from 'lucide-react'
import { motion } from 'framer-motion'
import { getArtifactType } from '@/lib/artifacts/utils.js'
import { useArtifactProcessingStatus } from '@/lib/artifacts/hooks/useArtifactProcessingStatus.js'

const ArtifactCard = ({
  artifact,
  isSelected,
  isExpanded,
  isEvaluating,
  canEvaluate,
  isActiveArtifact,
  onSelect,
  onToggleExpansion,
  onEvaluate,
  onDelete,
  onCardClick
}) => {
  // Track processing status for this artifact
  const { isProcessing, currentStage, statusBadge } = useArtifactProcessingStatus(
    artifact.id,
    true, // enabled
    3000 // poll every 3 seconds
  )
  const hasEvaluation = artifact.label !== null
  const confidence = artifact.confidence ? parseFloat(artifact.confidence) : 0
  const artifactType = getArtifactType(artifact.mime_type, artifact.uri)
  const IconComponent = artifactType.icon

  return (
    <motion.div
      key={artifact.id}
      layout
      initial={false}
      exit={{
        opacity: 0,
        scale: 0.3,
        rotate: 5,
      }}
      transition={{
        duration: 0.4,
        ease: [0.4, 0, 0.2, 1]
      }}
      style={{ position: 'relative' }}
      className="w-full box-border overflow-hidden"
    >
      <Card
        className={`cursor-pointer lgcustom-hover-transform transition-all gap-0 py-0 w-full max-w-full min-w-0 box-border overflow-hidden ${
          isActiveArtifact ? 'ring-2 ring-primary' : ''
        } ${isSelected ? 'ring-2 ring-primary/50' : ''} ${
          isEvaluating || isProcessing ? 'opacity-75' : ''
        }`}
        onClick={isProcessing ? undefined : onCardClick}
      >
        <CardHeader className="pb-2 pl-3 pr-4 pt-2.5 w-full max-w-full min-w-0 overflow-hidden box-border">
          <div className="flex items-start justify-between gap-2 w-full max-w-full box-border min-w-0 overflow-hidden">
            <div className="flex items-center flex-wrap gap-1.5 flex-1 min-w-0 overflow-hidden box-border max-w-[calc(100%-60px)]">
              <Checkbox
                checked={isSelected}
                onCheckedChange={onSelect}
                onClick={(e) => e.stopPropagation()}
                className="shrink-0 h-3.5 w-3.5"
              />
              
              {/* Artifact Type Badge */}
              <Badge 
                className={`text-xs shrink-0 px-1.5 py-0 flex items-center gap-0.5 whitespace-nowrap max-w-[4rem] ${artifactType.color}`}
                variant="outline"
                title={`Type: ${artifactType.label}`}
              >
                <IconComponent className="h-2.5 w-2.5 shrink-0" />
                <span className="truncate text-[10px]">{artifactType.label}</span>
              </Badge>
              
              {/* Processing Status Badge */}
              {statusBadge && isProcessing && (
                <Badge 
                  className={`text-xs shrink-0 px-1.5 py-0 flex items-center gap-0.5 whitespace-nowrap max-w-[5rem] ${
                    statusBadge.variant === 'default' 
                      ? 'bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-500/30' 
                      : statusBadge.variant === 'destructive'
                      ? 'bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/30'
                      : 'bg-muted text-muted-foreground border-border'
                  }`}
                  variant="outline"
                  title={`Processing: ${statusBadge.label}`}
                >
                  {statusBadge.spinning && <Loader2 className="h-2.5 w-2.5 shrink-0 animate-spin" />}
                  <span className="truncate text-[10px]">{statusBadge.label}</span>
                </Badge>
              )}
              
              {/* Evaluation Status Badge */}
              {hasEvaluation ? (
                <Badge 
                  className={`text-xs shrink-0 px-1.5 py-0 whitespace-nowrap max-w-[4rem] ${
                    artifact.label === 'Signal' 
                      ? 'bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/30' 
                      : artifact.label === 'Review'
                      ? 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 border-yellow-500/30'
                      : artifact.label === 'Noise'
                      ? 'bg-gray-500/20 text-gray-700 dark:text-gray-400 border-gray-500/30'
                      : 'bg-muted text-muted-foreground border-border'
                  }`}
                  variant="outline"
                >
                  <span className="truncate text-[10px]">{artifact.label}</span>
                </Badge>
              ) : (
                <Badge variant="outline" className="text-[10px] shrink-0 px-1.5 py-0 whitespace-nowrap bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/30 max-w-[5rem]">
                  <span className="truncate">Not Eval</span>
                </Badge>
              )}
            </div>
            
            {/* Action Buttons */}
            <div className="flex items-center shrink-0 gap-1 flex-nowrap" style={{ minWidth: '50px' }}>
              {isEvaluating || isProcessing ? (
                <Loader2 className="h-3 w-3 animate-spin text-primary shrink-0" />
              ) : canEvaluate ? (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 px-1.5 text-xs shrink-0"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEvaluate(artifact)
                  }}
                  disabled={isProcessing}
                  title="Evaluate Now"
                >
                  <PlayCircle className="h-3 w-3 text-primary" />
                </Button>
              ) : null}
              <Button
                variant="ghost"
                size="sm"
                className="h-5 w-5 p-0 shrink-0 text-red-500 dark:text-red-400 hover:text-red-400"
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete(artifact.id)
                }}
                disabled={isEvaluating || isProcessing}
                title={isProcessing ? 'Cannot delete while processing' : 'Delete artifact'}
              >
                <Trash2 className="h-3 w-3 !text-red-500 dark:!text-red-400" />
              </Button>
            </div>
          </div>
          
          <CardTitle className="text-xs font-medium line-clamp-1 mt-1.5 w-full max-w-full overflow-hidden text-ellipsis box-border break-words">
            {artifact.title || 'Untitled'}
          </CardTitle>
          <CardDescription className="text-xs line-clamp-1 mt-0.5 w-full max-w-full overflow-hidden text-ellipsis box-border break-words">
            {artifact.source || 'Unknown Source'}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="pt-0 pl-3 pr-4 pb-2.5 w-full max-w-full overflow-hidden box-border">
          {hasEvaluation ? (
            <Collapsible open={isExpanded} onOpenChange={onToggleExpansion}>
              <div className="space-y-2 w-full max-w-full box-border overflow-hidden">
                {/* Always visible: Date */}
                <div className="flex items-center justify-between text-xs text-muted-foreground w-full max-w-full box-border overflow-hidden">
                  <div className="flex items-center space-x-1 min-w-0 overflow-hidden">
                    <Clock className="h-3 w-3 shrink-0" />
                    <span className="truncate">{artifact.date}</span>
                  </div>
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-5 px-2 text-xs shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="h-3 w-3 mr-1 shrink-0" />
                          <span className="whitespace-nowrap">Less</span>
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-3 w-3 mr-1 shrink-0" />
                          <span className="whitespace-nowrap">More</span>
                        </>
                      )}
                    </Button>
                  </CollapsibleTrigger>
                </div>

                {/* Collapsible content */}
                <CollapsibleContent className="space-y-2">
                  {hasEvaluation && (
                    <div className="space-y-1 pt-1 border-t border-border">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">Confidence</span>
                        <span className="text-xs font-medium">{Math.round(confidence * 100)}%</span>
                      </div>
                      <Progress value={confidence * 100} className="h-1" />
                    </div>
                  )}
                  {artifact.topics && artifact.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1 border-t border-border">
                      {artifact.topics.map((topic, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CollapsibleContent>
              </div>
            </Collapsible>
          ) : (
            <div className="space-y-2 w-full max-w-full box-border overflow-hidden">
              {/* Always visible: Date (no expand/collapse for unevaluated) */}
              <div className="flex items-center text-xs text-muted-foreground min-w-0 overflow-hidden">
                <Clock className="h-3 w-3 mr-1 shrink-0" />
                <span className="truncate">{artifact.date}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default ArtifactCard

