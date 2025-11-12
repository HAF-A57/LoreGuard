import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible.jsx'
import { 
  TrendingUp, 
  FileText, 
  Globe, 
  Clock, 
  Activity,
  Users,
  Database,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  BarChart3,
  Loader2,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react'
import { API_URL } from '@/config.js'

const Dashboard = ({ onNavigateTo }) => {
  const [metrics, setMetrics] = useState({
    totalArtifacts: 0,
    todayProcessed: 0,
    signalArtifacts: 0,
    activeSources: 0,
    evaluationAccuracy: 0,
    processingSpeed: 0
  })
  const [recentActivity, setRecentActivity] = useState([])
  const [sourceStatus, setSourceStatus] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedArtifacts, setExpandedArtifacts] = useState(new Set())

  // Handle navigation to artifacts page with artifact selection
  const handleSeeDetails = (artifact) => {
    // Store artifact ID in localStorage for Artifacts component to pick up
    localStorage.setItem('loreguard_navigate_to_artifact', artifact.id)
    // Navigate to artifacts page
    if (onNavigateTo) {
      onNavigateTo('artifacts')
    }
  }

  // Helper function to format time ago
  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Unknown'
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now - date) / 1000)
    
    if (seconds < 60) return `${seconds} seconds ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
  }

  // Fetch dashboard data on mount
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch artifacts count
        const artifactsResponse = await fetch(`${API_URL}/api/v1/artifacts/?limit=1`)
        const artifactsData = await artifactsResponse.json()
        
        // Fetch evaluations for metrics
        const evaluationsResponse = await fetch(`${API_URL}/api/v1/evaluations/?limit=1000`)
        const evaluationsData = await evaluationsResponse.json()
        const evaluations = evaluationsData.items || []
        
        // Fetch sources
        const sourcesResponse = await fetch(`${API_URL}/api/v1/sources/`)
        const sourcesData = await sourcesResponse.json()
        const sources = sourcesData.items || []
        
        // Calculate metrics
        const totalArtifacts = artifactsData.total || 0
        const signalEvals = evaluations.filter(e => e.label === 'Signal')
        const signalArtifacts = signalEvals.length
        const activeSources = sources.filter(s => s.status === 'active').length
        
        // Calculate today's processed (evaluations created today)
        const today = new Date().toISOString().split('T')[0]
        const todayProcessed = evaluations.filter(e => 
          e.created_at && e.created_at.startsWith(today)
        ).length
        
        // Calculate accuracy (placeholder calculation)
        const evaluationAccuracy = evaluations.length > 0 
          ? Math.round((signalArtifacts + evaluations.filter(e => e.label === 'Review').length) / evaluations.length * 100)
          : 0

        setMetrics({
          totalArtifacts,
          todayProcessed,
          signalArtifacts,
          activeSources,
          evaluationAccuracy,
          processingSpeed: 156 // Placeholder - no tracking yet
        })

        // Recent activity (latest evaluations with full artifact data)
        // Fetch all artifacts for recent activity
        const allArtifactsResponse = await fetch(`${API_URL}/api/v1/artifacts/?limit=1000`)
        const allArtifactsData = allArtifactsResponse.ok ? await allArtifactsResponse.json() : { items: [] }
        const allArtifacts = allArtifactsData.items || []
        
        // Create evaluation map for quick lookup
        const evalMap = {}
        evaluations.forEach(ev => {
          if (ev.artifact_id && !evalMap[ev.artifact_id]) {
            evalMap[ev.artifact_id] = ev
          }
        })
        
        // Enrich artifacts with evaluation data and format titles
        const enrichedArtifacts = allArtifacts.map(artifact => {
          const evaluation = evalMap[artifact.id]
          
          let displayTitle = artifact.title
          if (!displayTitle) {
            const uriParts = artifact.uri?.split('/').filter(p => p && p.length > 3)
            const lastPart = uriParts?.[uriParts.length - 1] || ''
            displayTitle = lastPart
              .replace(/[-_]/g, ' ')
              .replace(/\.(html|htm|pdf|php)$/i, '')
              .substring(0, 60) || `Artifact ${artifact.id.substring(0, 8)}`
          }
          
          return {
            ...artifact,
            label: evaluation?.label || null,
            confidence: evaluation?.confidence || null,
            title: displayTitle,
            source: artifact.organization || 'Unknown Source',
            date: artifact.created_at ? new Date(artifact.created_at).toLocaleDateString() : 'Unknown',
            topics: artifact.topics || [],
            evaluationCreatedAt: evaluation?.created_at || null
          }
        })
        
        // Get recent evaluated artifacts (sorted by evaluation date, most recent first)
        const recentEvaluated = enrichedArtifacts
          .filter(a => a.label && a.evaluationCreatedAt)
          .sort((a, b) => new Date(b.evaluationCreatedAt) - new Date(a.evaluationCreatedAt))
          .slice(0, 10)
          .map(artifact => ({
            ...artifact,
            time: formatTimeAgo(artifact.evaluationCreatedAt)
          }))
        
        setRecentActivity(recentEvaluated)

        // Source status (sources with document counts)
        // Filter out deleted sources
        const nonDeletedSources = sources.filter(s => s.status !== 'deleted')
        const sourceStatusData = nonDeletedSources.slice(0, 10).map(source => ({
          name: source.name,
          status: source.status,
          docs: source.document_count || 0,
          health: 95 // Placeholder - no health tracking yet
        }))
        setSourceStatus(sourceStatusData)

      } catch (err) {
        console.error('Error fetching dashboard data:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  // Toggle artifact expansion
  const toggleArtifactExpansion = (artifactId) => {
    setExpandedArtifacts(prev => {
      const newSet = new Set(prev)
      if (newSet.has(artifactId)) {
        newSet.delete(artifactId)
      } else {
        newSet.add(artifactId)
      }
      return newSet
    })
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading dashboard...</p>
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
              <AlertTriangle className="h-5 w-5" />
              <span>Error Loading Dashboard</span>
            </CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">System overview and real-time metrics</p>
        </div>
        <div className="flex items-center space-x-2 bg-primary/10 rounded-lg px-3 py-2">
          <Activity className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">System Healthy</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Artifacts</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalArtifacts.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              +{metrics.todayProcessed} processed today
            </p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Signal Artifacts</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.signalArtifacts}</div>
            <p className="text-xs text-muted-foreground">
              High-value artifacts identified
            </p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Sources</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.activeSources}</div>
            <p className="text-xs text-muted-foreground">
              Monitoring global sources
            </p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Evaluation Accuracy</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.evaluationAccuracy}%</div>
            <Progress value={metrics.evaluationAccuracy} className="mt-2" />
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform relative">
          <span className="placeholder-card-indicator">⭐</span>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing Speed</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.processingSpeed}</div>
            <p className="text-xs text-muted-foreground">
              Artifacts per hour (not tracked yet)
            </p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform relative">
          <span className="placeholder-card-indicator">⭐</span>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Load</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">67%<span className="placeholder-indicator">⭐</span></div>
            <Progress value={67} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">Not tracked yet</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity and Source Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card className="aulendur-gradient-card">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5" />
              <span>Recent Activity</span>
            </CardTitle>
            <CardDescription>Latest artifact evaluations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentActivity.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No evaluations yet</p>
                </div>
              ) : (
                recentActivity.map((artifact) => {
                  const hasEvaluation = artifact.label !== null
                  const confidence = artifact.confidence ? parseFloat(artifact.confidence) : 0
                  const isExpanded = expandedArtifacts.has(artifact.id)
                  
                  return (
                    <Card
                      key={artifact.id}
                      className="cursor-pointer aulendur-hover-transform transition-all gap-0 py-0"
                    >
                      <CardHeader className="pb-2 px-3 pt-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center space-x-1.5 flex-1 min-w-0">
                            {hasEvaluation ? (
                              <Badge 
                                className={`text-xs shrink-0 px-1.5 py-0 ${
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
                                {artifact.label}
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-xs shrink-0 px-1.5 py-0 bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/30">Not Evaluated</Badge>
                            )}
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs shrink-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleSeeDetails(artifact)
                            }}
                            title="See Details"
                          >
                            <ExternalLink className="h-3 w-3" />
                          </Button>
                        </div>
                        <CardTitle className="text-xs font-medium line-clamp-1 mt-1.5">{artifact.title}</CardTitle>
                        <CardDescription className="text-xs line-clamp-1 mt-0.5">{artifact.source}</CardDescription>
                      </CardHeader>
                      <CardContent className="pt-0 px-3 pb-2.5">
                        {hasEvaluation ? (
                          <Collapsible open={isExpanded} onOpenChange={() => toggleArtifactExpansion(artifact.id)}>
                            <div className="space-y-2">
                              {/* Always visible: Date */}
                              <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <div className="flex items-center space-x-1">
                                  <Clock className="h-3 w-3" />
                                  <span>{artifact.time}</span>
                                </div>
                                <CollapsibleTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-5 px-2 text-xs"
                                  >
                                    {isExpanded ? (
                                      <>
                                        <ChevronUp className="h-3 w-3 mr-1" />
                                        Less
                                      </>
                                    ) : (
                                      <>
                                        <ChevronDown className="h-3 w-3 mr-1" />
                                        More
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
                          <div className="space-y-2">
                            {/* Always visible: Date */}
                            <div className="flex items-center text-xs text-muted-foreground">
                              <Clock className="h-3 w-3 mr-1" />
                              <span>{artifact.date}</span>
                  </div>
                </div>
                        )}
                      </CardContent>
                    </Card>
                  )
                })
              )}
            </div>
          </CardContent>
        </Card>

        {/* Source Status */}
        <Card className="aulendur-gradient-card">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Globe className="h-5 w-5" />
              <span>Source Health</span>
            </CardTitle>
            <CardDescription>Monitoring source performance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sourceStatus.map((source, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-background/50">
                  <div className="flex items-center space-x-3">
                    {source.status === 'active' ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : source.status === 'warning' ? (
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    ) : source.status === 'paused' ? (
                      <Clock className="h-4 w-4 text-gray-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <div>
                      <p className="text-sm font-medium">{source.name}</p>
                      <p className="text-xs text-muted-foreground">{source.docs} artifacts</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{source.health}%</div>
                    <Progress value={source.health} className="w-16 h-1" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard

