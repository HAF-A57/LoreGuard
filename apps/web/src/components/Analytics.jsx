import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  BarChart3, 
  TrendingUp, 
  Globe, 
  Clock, 
  Target,
  Users,
  Database,
  Zap,
  Award,
  Activity,
  MapPin,
  Calendar,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { API_URL } from '@/config.js'

const Analytics = () => {
  const [performanceMetrics, setPerformanceMetrics] = useState({
    totalArtifacts: 0,
    signalRate: 0,
    avgProcessingTime: 2.4, // Placeholder
    accuracyRate: 0,
    sourcesActive: 0,
    avgConfidence: 0
  })
  const [topSources, setTopSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch analytics data
  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch artifacts count
        const artifactsResponse = await fetch(`${API_URL}/api/v1/artifacts/?limit=1`)
        const artifactsData = await artifactsResponse.json()
        const totalArtifacts = artifactsData.total || 0

        // Fetch evaluations
        const evaluationsResponse = await fetch(`${API_URL}/api/v1/evaluations/?limit=1000`)
        const evaluationsData = await evaluationsResponse.json()
        const evaluations = evaluationsData.items || []

        // Fetch sources
        const sourcesResponse = await fetch(`${API_URL}/api/v1/sources/`)
        const sourcesData = await sourcesResponse.json()
        const sources = sourcesData.items || []

        // Calculate metrics
        const signalCount = evaluations.filter(e => e.label === 'Signal').length
        const signalRate = totalArtifacts > 0 ? ((signalCount / totalArtifacts) * 100).toFixed(1) : 0
        const avgConfidence = evaluations.length > 0
          ? evaluations.reduce((sum, e) => sum + (parseFloat(e.confidence) || 0), 0) / evaluations.length * 100
          : 0
        const accuracyRate = evaluations.length > 0
          ? ((evaluations.filter(e => e.label === 'Signal' || e.label === 'Review').length / evaluations.length) * 100).toFixed(1)
          : 0
        const sourcesActive = sources.filter(s => s.status === 'active').length

        setPerformanceMetrics({
          totalArtifacts,
          signalRate: parseFloat(signalRate),
          avgProcessingTime: 2.4, // Placeholder
          accuracyRate: parseFloat(accuracyRate),
          sourcesActive,
          avgConfidence: avgConfidence.toFixed(1)
        })

        // Calculate top sources
        const sourcesWithCounts = sources
          .map(s => ({
            name: s.name,
            artifacts: s.document_count || 0,
            signalRate: 12.0, // Placeholder
            avgConfidence: avgConfidence.toFixed(1)
          }))
          .sort((a, b) => b.artifacts - a.artifacts)
          .slice(0, 5)

        setTopSources(sourcesWithCounts)

      } catch (err) {
        console.error('Error fetching analytics:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [])

  // Placeholder data for features not yet calculated
  const topicDistribution = [
    { topic: "Defense & Security", count: 0, percentage: 0, trend: "N/A" },
  ]

  const geographicDistribution = [
    { region: "Not tracked yet", count: 0, percentage: 0, signalRate: 0 }
  ]

  const weeklyTrends = [
    { week: "Week 1", artifacts: 0, signals: 0, accuracy: 0 }
  ]

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading analytics...</p>
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
              <span>Error Loading Analytics</span>
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
                  <h1 className="text-3xl font-bold">Analytics</h1>
                  <p className="text-muted-foreground">Performance metrics and insights</p>
                </div>
        <div className="flex items-center space-x-2 bg-primary/10 rounded-lg px-3 py-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Performance Trending Up</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Artifacts</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceMetrics.totalArtifacts.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">All time processed</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Signal Rate</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceMetrics.signalRate}%</div>
            <p className="text-xs text-muted-foreground">High-value artifacts identified</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform relative">
          <span className="placeholder-card-indicator">⭐</span>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing Speed</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceMetrics.avgProcessingTime}s</div>
            <p className="text-xs text-muted-foreground">Average per artifact</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Accuracy Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceMetrics.accuracyRate}%</div>
            <Progress value={performanceMetrics.accuracyRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Sources</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceMetrics.sourcesActive}</div>
            <p className="text-xs text-muted-foreground">Monitoring globally</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceMetrics.avgConfidence}%</div>
            <Progress value={performanceMetrics.avgConfidence} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="sources" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="sources">Top Sources</TabsTrigger>
          <TabsTrigger value="topics">Topics</TabsTrigger>
          <TabsTrigger value="geography">Geography</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="sources" className="space-y-6">
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Top Performing Sources</span>
              </CardTitle>
              <CardDescription>Sources ranked by artifact volume and signal rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topSources.map((source, index) => (
                  <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-background/50">
                    <div className="flex items-center space-x-4">
                      <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                        <span className="text-sm font-bold">{index + 1}</span>
                      </div>
                      <div>
                        <div className="font-medium">{source.name}</div>
                        <div className="text-sm text-muted-foreground">{source.artifacts.toLocaleString()} artifacts</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <div className="text-lg font-bold text-primary">{source.signalRate}%</div>
                        <div className="text-xs text-muted-foreground">Signal Rate</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold">{source.avgConfidence}%</div>
                        <div className="text-xs text-muted-foreground">Avg Confidence</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="topics" className="space-y-6">
          <Card className="aulendur-gradient-card relative">
            <span className="placeholder-card-indicator">⭐</span>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Topic Distribution</span>
              </CardTitle>
              <CardDescription>Artifact categorization and trending topics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topicDistribution.map((topic, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="font-medium">{topic.topic}</span>
                        <Badge variant={topic.trend.startsWith('+') ? 'default' : 'secondary'}>
                          {topic.trend}
                        </Badge>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">{topic.count.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">{topic.percentage}%</div>
                      </div>
                    </div>
                    <Progress value={topic.percentage} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="geography" className="space-y-6">
          <Card className="aulendur-gradient-card relative">
            <span className="placeholder-card-indicator">⭐</span>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <MapPin className="h-5 w-5" />
                <span>Geographic Distribution</span>
              </CardTitle>
              <CardDescription>Artifact sources by geographic region</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {geographicDistribution.map((region, index) => (
                  <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-background/50">
                    <div className="flex items-center space-x-3">
                      <Globe className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{region.region}</div>
                        <div className="text-sm text-muted-foreground">{region.count.toLocaleString()} artifacts</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <div className="text-lg font-bold">{region.percentage}%</div>
                        <div className="text-xs text-muted-foreground">Share</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-primary">{region.signalRate}%</div>
                        <div className="text-xs text-muted-foreground">Signal Rate</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <Card className="aulendur-gradient-card relative">
            <span className="placeholder-card-indicator">⭐</span>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Calendar className="h-5 w-5" />
                <span>Weekly Performance Trends</span>
              </CardTitle>
              <CardDescription>Performance metrics over the last 4 weeks</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {weeklyTrends.map((week, index) => (
                  <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-background/50">
                    <div className="font-medium">{week.week}</div>
                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <div className="text-lg font-bold">{week.artifacts.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">Artifacts</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-primary">{week.signals}</div>
                        <div className="text-xs text-muted-foreground">Signals</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold">{week.accuracy}%</div>
                        <div className="text-xs text-muted-foreground">Accuracy</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Analytics

