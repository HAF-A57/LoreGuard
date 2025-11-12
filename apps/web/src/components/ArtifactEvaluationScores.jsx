import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import InfoTooltip from '@/components/InfoTooltip.jsx'
import { Star, TrendingUp, AlertCircle } from 'lucide-react'

const ArtifactEvaluationScores = ({ evaluation, rubric }) => {
  if (!evaluation || !evaluation.scores) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Evaluation Scores</CardTitle>
          <CardDescription>No evaluation data available</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const scores = evaluation.scores || {}
  const categories = rubric?.categories || {}
  const thresholds = rubric?.thresholds || {}
  
  // Calculate total score if not provided
  const totalScore = evaluation.total_score || Object.values(scores).reduce((sum, scoreData) => {
    const score = typeof scoreData === 'object' ? scoreData.score : scoreData
    const categoryName = Object.keys(scores).find(key => scores[key] === scoreData)
    const weight = categories[categoryName]?.weight || 0
    return sum + (score * weight)
  }, 0)

  const getScoreColor = (score) => {
    if (score >= (thresholds.signal_min || 3.8)) return 'text-green-600 dark:text-green-400'
    if (score >= (thresholds.review_min || 2.8)) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getScoreVariant = (score) => {
    if (score >= (thresholds.signal_min || 3.8)) return 'default'
    if (score >= (thresholds.review_min || 2.8)) return 'secondary'
    return 'outline'
  }

  return (
    <div className="space-y-4">
      {/* Overall Score Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5" />
                <span>Overall Evaluation</span>
              </CardTitle>
              <CardDescription className="mt-1">
                Rubric: {evaluation.rubric_version || 'Unknown'} • Model: {evaluation.model_id || 'Unknown'}
              </CardDescription>
            </div>
            <div className="text-right">
              <div className={`text-2xl font-bold ${getScoreColor(totalScore)}`}>
                {totalScore.toFixed(2)}
              </div>
              <div className="text-sm text-muted-foreground">Total Score</div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Classification</span>
              <Badge variant={getScoreVariant(totalScore)}>
                {evaluation.label || 'Not Classified'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Confidence</span>
              <div className="flex items-center space-x-2">
                <Progress value={evaluation.confidence * 100} className="w-24 h-2" />
                <span className="text-sm font-medium w-12 text-right">
                  {Math.round(evaluation.confidence * 100)}%
                </span>
              </div>
            </div>
            {evaluation.created_at && (
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Evaluated</span>
                <span>{new Date(evaluation.created_at).toLocaleString()}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Category Scores */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Star className="h-5 w-5" />
            <span>Category Scores</span>
          </CardTitle>
          <CardDescription>
            Detailed scores for each evaluation category
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(scores).map(([categoryName, scoreData]) => {
              const score = typeof scoreData === 'object' ? scoreData.score : scoreData
              const reasoning = typeof scoreData === 'object' ? scoreData.reasoning : null
              const categoryInfo = categories[categoryName] || {}
              const weight = categoryInfo.weight || 0
              const description = categoryInfo.description || categoryInfo.guidance || ''

              return (
                <div key={categoryName}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-semibold capitalize">
                          {categoryName.replace(/_/g, ' ')}
                        </h4>
                        {description && (
                          <InfoTooltip content={description} />
                        )}
                        {weight > 0 && (
                          <Badge variant="outline" className="text-xs">
                            Weight: {weight}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="text-right ml-4">
                      <div className={`text-xl font-bold ${getScoreColor(score)}`}>
                        {score.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground">/ 5.00</div>
                    </div>
                  </div>
                  
                  <Progress 
                    value={(score / 5) * 100} 
                    className="h-2 mb-2"
                  />
                  
                  {reasoning && (
                    <div className="mt-2 p-3 bg-muted/50 rounded-md">
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {reasoning}
                      </p>
                    </div>
                  )}
                  
                  {Object.entries(scores).indexOf([categoryName, scoreData]) < Object.entries(scores).length - 1 && (
                    <Separator className="mt-4" />
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Thresholds Info */}
      {thresholds && (thresholds.signal_min || thresholds.review_min) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-sm">
              <AlertCircle className="h-4 w-4" />
              <span>Classification Thresholds</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">Signal</div>
                <div className="font-semibold text-green-600 dark:text-green-400">
                  ≥ {thresholds.signal_min || 3.8}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground">Review</div>
                <div className="font-semibold text-yellow-600 dark:text-yellow-400">
                  ≥ {thresholds.review_min || 2.8}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground">Noise</div>
                <div className="font-semibold text-red-600 dark:text-red-400">
                  &lt; {thresholds.review_min || 2.8}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ArtifactEvaluationScores

