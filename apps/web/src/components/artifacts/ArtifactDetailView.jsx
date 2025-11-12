/**
 * ArtifactDetailView Component
 * Main content area showing detailed artifact information
 * Displays header with metadata and tabbed content (Metadata, Content, Evaluations)
 */

import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  FileText, 
  Clock, 
  Loader2,
  Info,
  FileCode,
  BarChart3,
  PlayCircle
} from 'lucide-react'
import ArtifactMetadata from '@/components/ArtifactMetadata.jsx'
import ArtifactNormalizedContent from '@/components/ArtifactNormalizedContent.jsx'
import ArtifactEvaluationScores from '@/components/ArtifactEvaluationScores.jsx'

const ArtifactDetailView = ({
  selectedArtifact,
  selectedArtifactDetails,
  normalizedContent,
  contentLoading,
  contentError,
  evaluations,
  evaluationsLoading,
  evaluationReadiness,
  evaluatingArtifacts,
  onStartEvaluation
}) => {
  if (!selectedArtifact) {
    return (
      <main className="flex-1 flex flex-col min-h-0 h-full overflow-hidden">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Select an Artifact</h3>
            <p className="text-muted-foreground">Choose an artifact from the sidebar to view its details</p>
          </div>
        </div>
      </main>
    )
  }

  const latestEvaluation = evaluations && evaluations.length > 0 ? evaluations[0] : null
  const rubric = latestEvaluation?.rubric || null
  const isEvaluating = evaluatingArtifacts.has(selectedArtifact.id)
  const canEvaluate = !selectedArtifact.label && 
                      evaluationReadiness[selectedArtifact.id]?.ready === true &&
                      !isEvaluating

  return (
    <main className="flex-1 flex flex-col min-h-0 h-full overflow-hidden">
      {/* Content Header */}
      <div className="p-6 border-b border-border bg-card flex-shrink-0">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              {selectedArtifact.label ? (
                <Badge 
                  className={
                    selectedArtifact.label === 'Signal' 
                      ? 'bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/30' 
                      : selectedArtifact.label === 'Review'
                      ? 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 border-yellow-500/30'
                      : selectedArtifact.label === 'Noise'
                      ? 'bg-gray-500/20 text-gray-700 dark:text-gray-400 border-gray-500/30'
                      : 'bg-muted text-muted-foreground border-border'
                  }
                  variant="outline"
                >
                  {selectedArtifact.label}
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/30">
                  Not Evaluated
                </Badge>
              )}
              <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>{selectedArtifact.date}</span>
              </div>
            </div>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">{selectedArtifact.title}</h2>
                <p className="text-muted-foreground mb-3">{selectedArtifact.source}</p>
                {selectedArtifact.topics && selectedArtifact.topics.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {selectedArtifact.topics.map((topic, idx) => (
                      <Badge key={idx} variant="outline">
                        {topic}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              {canEvaluate && (
                <Button
                  onClick={() => onStartEvaluation(selectedArtifact)}
                  className="ml-4"
                >
                  <PlayCircle className="h-4 w-4 mr-2" />
                  Evaluate Now
                </Button>
              )}
              {isEvaluating && (
                <div className="ml-4 flex items-center space-x-2 text-primary">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Evaluating...</span>
                </div>
              )}
            </div>
          </div>
          {latestEvaluation && (
            <div className="flex items-center space-x-2 ml-6">
              <div className="text-right">
                <div className="text-sm text-muted-foreground">Confidence Score</div>
                <div className="text-2xl font-bold text-primary">
                  {Math.round(latestEvaluation.confidence * 100)}%
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Content Body with Tabs */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <Tabs defaultValue="metadata" className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="px-6 pt-4 border-b border-border">
            <TabsList>
              <TabsTrigger value="metadata" className="flex items-center space-x-2">
                <Info className="h-4 w-4" />
                <span>Metadata</span>
              </TabsTrigger>
              <TabsTrigger value="content" className="flex items-center space-x-2">
                <FileCode className="h-4 w-4" />
                <span>Content</span>
              </TabsTrigger>
              <TabsTrigger value="evaluations" className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4" />
                <span>Evaluations</span>
                {evaluations.length > 0 && (
                  <Badge variant="secondary" className="ml-1">{evaluations.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea className="flex-1 min-h-0">
            <div className="p-6">
              <TabsContent value="metadata" className="mt-0 space-y-4">
                <ArtifactMetadata 
                  artifact={selectedArtifactDetails}
                  metadata={selectedArtifactDetails?.document_metadata}
                  clarification={selectedArtifactDetails?.clarification}
                />
              </TabsContent>

              <TabsContent value="content" className="mt-0">
                <ArtifactNormalizedContent
                  content={normalizedContent}
                  loading={contentLoading}
                  error={contentError}
                  contentLength={normalizedContent?.length}
                />
              </TabsContent>

              <TabsContent value="evaluations" className="mt-0 space-y-4">
                {evaluationsLoading ? (
                  <Card>
                    <CardContent className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                      <span className="ml-2 text-muted-foreground">Loading evaluations...</span>
                    </CardContent>
                  </Card>
                ) : evaluations.length === 0 ? (
                  <Card>
                    <CardHeader>
                      <CardTitle>Evaluations</CardTitle>
                      <CardDescription>No evaluations available for this artifact</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-muted-foreground">
                        This artifact has not been evaluated yet. Use the evaluation endpoint to evaluate it.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  evaluations.map((evaluation, idx) => (
                    <ArtifactEvaluationScores
                      key={evaluation.id || idx}
                      evaluation={evaluation}
                      rubric={evaluation.rubric || rubric}
                    />
                  ))
                )}
              </TabsContent>
            </div>
          </ScrollArea>
        </Tabs>
      </div>
    </main>
  )
}

export default ArtifactDetailView

