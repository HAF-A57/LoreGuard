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
  Calendar
} from 'lucide-react'

const Analytics = () => {
  // Mock data for analytics
  const performanceMetrics = {
    totalDocuments: 45892,
    signalRate: 12.3,
    avgProcessingTime: 2.4,
    accuracyRate: 94.2,
    sourcesActive: 47,
    avgConfidence: 78.6
  }

  const topSources = [
    { name: "NATO Strategic Communications", documents: 8934, signalRate: 15.2, avgConfidence: 82.1 },
    { name: "International Economic Forum", documents: 6721, signalRate: 11.8, avgConfidence: 79.3 },
    { name: "Cybersecurity Research Institute", documents: 5643, signalRate: 14.7, avgConfidence: 81.5 },
    { name: "Defense Policy Institute", documents: 4892, signalRate: 9.4, avgConfidence: 76.8 },
    { name: "Regional Security Council", documents: 3756, signalRate: 13.1, avgConfidence: 80.2 }
  ]

  const topicDistribution = [
    { topic: "Defense & Security", count: 12847, percentage: 28.0, trend: "+5.2%" },
    { topic: "Economic Analysis", count: 9234, percentage: 20.1, trend: "+2.8%" },
    { topic: "Cybersecurity", count: 7891, percentage: 17.2, trend: "+8.1%" },
    { topic: "Regional Politics", count: 6543, percentage: 14.3, trend: "-1.4%" },
    { topic: "Technology", count: 4892, percentage: 10.7, trend: "+12.3%" },
    { topic: "Other", count: 4485, percentage: 9.8, trend: "+0.9%" }
  ]

  const geographicDistribution = [
    { region: "Europe", count: 15234, percentage: 33.2, signalRate: 13.8 },
    { region: "North America", count: 12891, percentage: 28.1, signalRate: 11.2 },
    { region: "Asia-Pacific", count: 8934, percentage: 19.5, signalRate: 12.9 },
    { region: "Middle East", count: 5643, percentage: 12.3, signalRate: 14.7 },
    { region: "Africa", count: 2134, percentage: 4.7, signalRate: 10.3 },
    { region: "South America", count: 1056, percentage: 2.3, signalRate: 9.1 }
  ]

  const weeklyTrends = [
    { week: "Week 1", documents: 8934, signals: 1098, accuracy: 93.2 },
    { week: "Week 2", documents: 9234, signals: 1156, accuracy: 94.1 },
    { week: "Week 3", documents: 8756, signals: 1089, accuracy: 93.8 },
    { week: "Week 4", documents: 9567, signals: 1234, accuracy: 94.7 }
  ]

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
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceMetrics.totalDocuments.toLocaleString()}</div>
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
            <p className="text-xs text-muted-foreground">High-value documents identified</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing Speed</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{performanceMetrics.avgProcessingTime}s</div>
            <p className="text-xs text-muted-foreground">Average per document</p>
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
              <CardDescription>Sources ranked by document volume and signal rate</CardDescription>
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
                        <div className="text-sm text-muted-foreground">{source.documents.toLocaleString()} documents</div>
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
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Topic Distribution</span>
              </CardTitle>
              <CardDescription>Document categorization and trending topics</CardDescription>
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
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <MapPin className="h-5 w-5" />
                <span>Geographic Distribution</span>
              </CardTitle>
              <CardDescription>Document sources by geographic region</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {geographicDistribution.map((region, index) => (
                  <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-background/50">
                    <div className="flex items-center space-x-3">
                      <Globe className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{region.region}</div>
                        <div className="text-sm text-muted-foreground">{region.count.toLocaleString()} documents</div>
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
          <Card className="aulendur-gradient-card">
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
                        <div className="text-lg font-bold">{week.documents.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">Documents</div>
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

