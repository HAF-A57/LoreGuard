import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { 
  Target, 
  BarChart3, 
  Settings, 
  CheckCircle, 
  AlertCircle,
  TrendingUp,
  Brain,
  Zap,
  Clock,
  Award,
  Edit,
  Plus,
  Trash2,
  Loader2,
  Eye,
  FileText
} from 'lucide-react'
import { API_URL } from '@/config.js'
import RubricDetailModal from './RubricDetailModal.jsx'
import RubricFormModal from './RubricFormModal.jsx'
import RubricNarrativeModal from './RubricNarrativeModal.jsx'
import PromptTemplates from './PromptTemplates.jsx'

const Evaluations = () => {
  // Component for managing evaluations and rubrics
  const [rubrics, setRubrics] = useState([])
  const [activeRubric, setActiveRubric] = useState(null)
  const [evaluations, setEvaluations] = useState([])
  const [viewingRubricId, setViewingRubricId] = useState(null)
  const [isRubricModalOpen, setIsRubricModalOpen] = useState(false)
  const [editingRubricId, setEditingRubricId] = useState(null)
  const [isFormModalOpen, setIsFormModalOpen] = useState(false)
  const [narrativeRubricId, setNarrativeRubricId] = useState(null)
  const [isNarrativeModalOpen, setIsNarrativeModalOpen] = useState(false)
  const [evaluationStats, setEvaluationStats] = useState({
    total: 0,
    signal: 0,
    review: 0,
    noise: 0,
    avgConfidence: 0
  })
  const [dailyStats, setDailyStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch rubrics and active rubric
  useEffect(() => {
    const fetchRubrics = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch all rubrics
        const rubricsResponse = await fetch(`${API_URL}/api/v1/rubrics/`)
        if (!rubricsResponse.ok) throw new Error('Failed to fetch rubrics')
        const rubricsData = await rubricsResponse.json()
        setRubrics(rubricsData.items || [])

        // Fetch active rubric
        try {
          const activeResponse = await fetch(`${API_URL}/api/v1/rubrics/active`)
          if (activeResponse.ok) {
            const activeData = await activeResponse.json()
            setActiveRubric(activeData)
          }
        } catch (err) {
          console.warn('No active rubric found:', err)
        }
      } catch (err) {
        console.error('Error fetching rubrics:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchRubrics()
  }, [])

  // Fetch evaluations and calculate stats
  useEffect(() => {
    const fetchEvaluations = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/evaluations/?limit=1000`)
        if (!response.ok) throw new Error('Failed to fetch evaluations')
        const data = await response.json()
        const evals = data.items || []
        setEvaluations(evals)

        // Calculate overall stats
        const total = evals.length
        const signal = evals.filter(e => e.label === 'Signal').length
        const review = evals.filter(e => e.label === 'Review').length
        const noise = evals.filter(e => e.label === 'Noise').length
        const confidences = evals
          .map(e => e.confidence ? parseFloat(e.confidence) : 0)
          .filter(c => c > 0)
        const avgConfidence = confidences.length > 0
          ? (confidences.reduce((a, b) => a + b, 0) / confidences.length) * 100
          : 0

        setEvaluationStats({
          total,
          signal,
          review,
          noise,
          avgConfidence: Math.round(avgConfidence * 10) / 10
        })

        // Calculate daily stats
        const dailyMap = new Map()
        evals.forEach(evaluation => {
          const date = new Date(evaluation.created_at).toISOString().split('T')[0]
          if (!dailyMap.has(date)) {
            dailyMap.set(date, { date, total: 0, signal: 0, review: 0, noise: 0, confidences: [] })
          }
          const day = dailyMap.get(date)
          day.total++
          if (evaluation.label === 'Signal') day.signal++
          else if (evaluation.label === 'Review') day.review++
          else if (evaluation.label === 'Noise') day.noise++
          if (evaluation.confidence) day.confidences.push(parseFloat(evaluation.confidence))
        })

        const daily = Array.from(dailyMap.values())
          .map(day => ({
            date: day.date,
            total: day.total,
            signal: day.signal,
            review: day.review,
            noise: day.noise,
            avgConfidence: day.confidences.length > 0
              ? Math.round((day.confidences.reduce((a, b) => a + b, 0) / day.confidences.length) * 1000) / 10
              : 0
          }))
          .sort((a, b) => b.date.localeCompare(a.date))
          .slice(0, 7) // Last 7 days

        setDailyStats(daily)
      } catch (err) {
        console.error('Error fetching evaluations:', err)
      }
    }

    fetchEvaluations()
  }, [])

  const handleActivateRubric = async (rubricId) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/rubrics/${rubricId}/activate`, {
        method: 'PUT'
      })
      if (!response.ok) throw new Error('Failed to activate rubric')
      const updated = await response.json()
      setActiveRubric(updated)
      // Refresh rubrics list
      const rubricsResponse = await fetch(`${API_URL}/api/v1/rubrics/`)
      const rubricsData = await rubricsResponse.json()
      setRubrics(rubricsData.items || [])
    } catch (err) {
      console.error('Error activating rubric:', err)
      alert('Failed to activate rubric: ' + err.message)
    }
  }

  const handleDeleteRubric = async (rubricId) => {
    if (!confirm('Are you sure you want to delete this rubric? This action cannot be undone.')) {
      return
    }
    try {
      const response = await fetch(`${API_URL}/api/v1/rubrics/${rubricId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to delete rubric')
      // Refresh rubrics list
      const rubricsResponse = await fetch(`${API_URL}/api/v1/rubrics/`)
      const rubricsData = await rubricsResponse.json()
      setRubrics(rubricsData.items || [])
    } catch (err) {
      console.error('Error deleting rubric:', err)
      alert('Failed to delete rubric: ' + err.message)
    }
  }

  const handleNewRubric = () => {
    setEditingRubricId(null)
    setIsFormModalOpen(true)
  }

  const handleEditRubric = (rubricId) => {
    setEditingRubricId(rubricId)
    setIsFormModalOpen(true)
  }

  const handleFormSuccess = async () => {
    // Refresh rubrics list
    try {
      const response = await fetch(`${API_URL}/api/v1/rubrics/`)
      if (response.ok) {
        const data = await response.json()
        setRubrics(data.items || [])
      }
      
      // Refresh active rubric
      try {
        const activeResponse = await fetch(`${API_URL}/api/v1/rubrics/active`)
        if (activeResponse.ok) {
          const activeData = await activeResponse.json()
          setActiveRubric(activeData)
        }
      } catch (err) {
        console.warn('No active rubric found:', err)
        setActiveRubric(null)
      }
    } catch (err) {
      console.error('Error refreshing rubrics:', err)
    }
  }

  const handleViewRubricDetails = (rubricId) => {
    setViewingRubricId(rubricId)
    setIsRubricModalOpen(true)
  }

  // Format category name for display
  const formatCategoryName = (key) => {
    return key.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  // Get category weight percentage
  const getCategoryWeight = (category) => {
    return Math.round((category.weight || 0) * 100)
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading rubrics and evaluations...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <span>Error Loading Data</span>
            </CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  // Get full active rubric data
  let activeRubricData = activeRubric && typeof activeRubric === 'object' 
    ? activeRubric 
    : (activeRubric ? rubrics.find(r => r.id === activeRubric || r.version === activeRubric) : null)
  
  // Ensure we have the ID for the active rubric (from API response or from list)
  if (activeRubricData && !activeRubricData.id && activeRubricData.version) {
    const foundRubric = rubrics.find(r => r.version === activeRubricData.version)
    if (foundRubric) {
      activeRubricData = { ...activeRubricData, id: foundRubric.id }
    }
  }
  
  // Handle categories as array or object
  const categories = activeRubricData?.categories 
    ? (Array.isArray(activeRubricData.categories)
        ? activeRubricData.categories.map((cat, idx) => [cat.id || `category_${idx}`, cat])
        : Object.entries(activeRubricData.categories))
    : []

  // Calculate today's stats
  const today = new Date().toISOString().split('T')[0]
  const todayStats = dailyStats.find(s => s.date === today) || {
    total: 0,
    signal: 0,
    review: 0,
    noise: 0,
    avgConfidence: 0
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Evaluations</h1>
          <p className="text-muted-foreground">Rubric management and evaluation performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={() => window.location.hash = '#/settings'}>
            <Settings className="h-4 w-4 mr-2" />
            Configure Models
          </Button>
          <Button size="sm" onClick={handleNewRubric}>
            <Plus className="h-4 w-4 mr-2" />
            New Rubric
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="rubrics">Rubrics</TabsTrigger>
          <TabsTrigger value="meta-prompts">Meta-Prompts</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Current Rubric Status */}
          {activeRubricData ? (
            <Card className="aulendur-gradient-card">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5" />
                  <span>Active Rubric</span>
                </CardTitle>
                <CardDescription>Currently deployed evaluation criteria</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">Rubric {activeRubricData.version}</h3>
                    <p className="text-sm text-muted-foreground">Version {activeRubricData.version}</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge variant="default" className="bg-green-500">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Active
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewRubricDetails(activeRubricData.id)}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                </div>
                {categories.length > 0 && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      {categories.map(([key, category]) => (
                        <div 
                          key={key} 
                          className="text-center p-3 rounded-lg bg-background/50 hover:bg-background/70 cursor-pointer transition-colors"
                          onClick={() => handleViewRubricDetails(activeRubricData.id)}
                          title={`Click to view details about ${formatCategoryName(key)}`}
                        >
                          <div className="text-lg font-bold">{getCategoryWeight(category)}%</div>
                          <div className="text-xs text-muted-foreground">{formatCategoryName(key)}</div>
                          {category.guidance && (
                            <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {category.guidance}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    <div className="text-xs text-muted-foreground text-center pt-2">
                      Click any category to view full rubric details
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>No Active Rubric</CardTitle>
                <CardDescription>Please activate a rubric to start evaluations</CardDescription>
              </CardHeader>
            </Card>
          )}

          {/* Today's Evaluation Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="aulendur-hover-transform">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Artifacts Evaluated</CardTitle>
                <Brain className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{evaluationStats.total}</div>
                <p className="text-xs text-muted-foreground">
                  {todayStats.total > 0 ? `${todayStats.total} today` : 'Total'}
                </p>
              </CardContent>
            </Card>

            <Card className="aulendur-hover-transform">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Signal Identified</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{evaluationStats.signal}</div>
                <p className="text-xs text-muted-foreground">
                  {evaluationStats.total > 0 
                    ? `${Math.round((evaluationStats.signal / evaluationStats.total) * 1000) / 10}% of total`
                    : '0%'}
                </p>
              </CardContent>
            </Card>

            <Card className="aulendur-hover-transform">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
                <Award className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{evaluationStats.avgConfidence}%</div>
                <p className="text-xs text-muted-foreground">Overall average</p>
              </CardContent>
            </Card>

            <Card className="aulendur-hover-transform">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Review Items</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{evaluationStats.review}</div>
                <p className="text-xs text-muted-foreground">Requires review</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="rubrics" className="space-y-6">
          {rubrics.length === 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>No Rubrics</CardTitle>
                <CardDescription>Create your first rubric to get started</CardDescription>
              </CardHeader>
              <CardContent>
                <Button onClick={handleNewRubric}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Rubric
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-6">
              {rubrics.map((rubric) => {
                // Handle categories as array or object
                const rubricCategories = rubric.categories 
                  ? (Array.isArray(rubric.categories)
                      ? rubric.categories.map((cat, idx) => [cat.id || `category_${idx}`, cat])
                      : Object.entries(rubric.categories))
                  : []
                return (
                  <Card key={rubric.id || rubric.version} className="aulendur-hover-transform">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="flex items-center space-x-2">
                            <span>Rubric {rubric.version}</span>
                            <Badge variant={rubric.is_active ? 'default' : 'secondary'}>
                              {rubric.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </CardTitle>
                          <CardDescription>
                            Version {rubric.version} • Created {new Date(rubric.created_at).toLocaleDateString()}
                          </CardDescription>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleViewRubricDetails(rubric.id)}
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => {
                              setNarrativeRubricId(rubric.id)
                              setIsNarrativeModalOpen(true)
                            }}
                          >
                            <FileText className="h-4 w-4 mr-2" />
                            View Narrative
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleEditRubric(rubric.id)}
                          >
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </Button>
                          {!rubric.is_active && (
                            <Button 
                              size="sm"
                              onClick={() => handleActivateRubric(rubric.id)}
                            >
                              Activate
                            </Button>
                          )}
                          {!rubric.is_active && (
                            <Button 
                              variant="destructive" 
                              size="sm"
                              onClick={() => handleDeleteRubric(rubric.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {rubricCategories.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="font-semibold text-sm">Evaluation Categories</h4>
                          <div className="grid gap-3">
                            {rubricCategories.map(([key, category]) => (
                              <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                                <div>
                                  <div className="font-medium text-sm">{formatCategoryName(key)}</div>
                                  <div className="text-xs text-muted-foreground">
                                    {category.guidance || 'No description'}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="font-bold">{getCategoryWeight(category)}%</div>
                                  <div className="text-xs text-muted-foreground">Weight</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="meta-prompts" className="space-y-6">
          <PromptTemplates />
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Evaluation Performance</span>
              </CardTitle>
              <CardDescription>Daily evaluation results and trends</CardDescription>
            </CardHeader>
            <CardContent>
              {dailyStats.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No evaluation data available yet
                </div>
              ) : (
                <ScrollArea className="h-64">
                  <div className="space-y-3">
                    {dailyStats.map((result, index) => (
                      <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-background/50">
                        <div className="flex items-center space-x-4">
                          <div>
                            <div className="font-medium">{new Date(result.date).toLocaleDateString()}</div>
                            <div className="text-sm text-muted-foreground">{result.total} artifacts</div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-6">
                          <div className="text-center">
                            <div className="text-lg font-bold text-green-600">{result.signal}</div>
                            <div className="text-xs text-muted-foreground">Signal</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-yellow-600">{result.review}</div>
                            <div className="text-xs text-muted-foreground">Review</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-gray-600">{result.noise}</div>
                            <div className="text-xs text-muted-foreground">Noise</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold">{result.avgConfidence}%</div>
                            <div className="text-xs text-muted-foreground">Avg Confidence</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Rubric Detail Modal */}
      <RubricDetailModal
        rubricId={viewingRubricId}
        open={isRubricModalOpen}
        onOpenChange={setIsRubricModalOpen}
        onViewNarrative={(id) => {
          setNarrativeRubricId(id)
          setIsNarrativeModalOpen(true)
        }}
      />

      {/* Rubric Form Modal (Create/Edit) */}
      <RubricFormModal
        rubricId={editingRubricId}
        open={isFormModalOpen}
        onOpenChange={setIsFormModalOpen}
        onSuccess={handleFormSuccess}
      />

      {/* Rubric Narrative Modal */}
      <RubricNarrativeModal
        rubricId={narrativeRubricId}
        open={isNarrativeModalOpen}
        onOpenChange={setIsNarrativeModalOpen}
      />
    </div>
  )
}

export default Evaluations

