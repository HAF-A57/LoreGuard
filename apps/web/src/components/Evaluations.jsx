import { useState } from 'react'
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
  Plus
} from 'lucide-react'

const Evaluations = () => {
  const [activeRubric, setActiveRubric] = useState("v2.1")

  // Mock data for rubrics
  const rubrics = [
    {
      version: "v2.1",
      name: "Military Wargaming Relevance Rubric",
      status: "active",
      created: "2024-09-01",
      accuracy: 94.2,
      categories: [
        { name: "Strategic Relevance", weight: 30, description: "Relevance to military strategy and wargaming scenarios" },
        { name: "Source Credibility", weight: 25, description: "Reliability and authority of the information source" },
        { name: "Temporal Relevance", weight: 20, description: "Timeliness and currency of the information" },
        { name: "Geographic Scope", weight: 15, description: "Geographic relevance to areas of interest" },
        { name: "Actionable Intelligence", weight: 10, description: "Potential for informing strategic decisions" }
      ]
    },
    {
      version: "v2.0",
      name: "Military Wargaming Relevance Rubric",
      status: "archived",
      created: "2024-08-15",
      accuracy: 91.8,
      categories: [
        { name: "Strategic Relevance", weight: 35, description: "Relevance to military strategy and wargaming scenarios" },
        { name: "Source Credibility", weight: 30, description: "Reliability and authority of the information source" },
        { name: "Temporal Relevance", weight: 20, description: "Timeliness and currency of the information" },
        { name: "Geographic Scope", weight: 15, description: "Geographic relevance to areas of interest" }
      ]
    }
  ]

  // Mock evaluation results
  const evaluationResults = [
    { date: "2024-09-10", total: 156, signal: 23, review: 89, noise: 44, avgConfidence: 76.3 },
    { date: "2024-09-09", total: 142, signal: 19, review: 78, noise: 45, avgConfidence: 74.8 },
    { date: "2024-09-08", total: 167, signal: 28, review: 94, noise: 45, avgConfidence: 78.1 },
    { date: "2024-09-07", total: 134, signal: 21, review: 71, noise: 42, avgConfidence: 75.9 }
  ]

  const currentRubric = rubrics.find(r => r.version === activeRubric)

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Evaluations</h1>
          <p className="text-muted-foreground">Rubric management and evaluation performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Configure Models
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Rubric
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="rubrics">Rubrics</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Current Rubric Status */}
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
                  <h3 className="text-lg font-semibold">{currentRubric?.name}</h3>
                  <p className="text-sm text-muted-foreground">Version {currentRubric?.version}</p>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-2xl font-bold text-primary">{currentRubric?.accuracy}%</div>
                    <div className="text-xs text-muted-foreground">Accuracy</div>
                  </div>
                  <Badge variant="default" className="bg-green-500">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                </div>
              </div>
              <Progress value={currentRubric?.accuracy} className="mb-4" />
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {currentRubric?.categories.map((category, index) => (
                  <div key={index} className="text-center p-3 rounded-lg bg-background/50">
                    <div className="text-lg font-bold">{category.weight}%</div>
                    <div className="text-xs text-muted-foreground">{category.name}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Today's Evaluation Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="aulendur-hover-transform">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Documents Evaluated</CardTitle>
                <Brain className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">156</div>
                <p className="text-xs text-muted-foreground">Today</p>
              </CardContent>
            </Card>

            <Card className="aulendur-hover-transform">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Signal Identified</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">23</div>
                <p className="text-xs text-muted-foreground">14.7% of total</p>
              </CardContent>
            </Card>

            <Card className="aulendur-hover-transform">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
                <Award className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">76.3%</div>
                <p className="text-xs text-muted-foreground">+1.5% from yesterday</p>
              </CardContent>
            </Card>

            <Card className="aulendur-hover-transform">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Processing Speed</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">2.3s</div>
                <p className="text-xs text-muted-foreground">Avg per document</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="rubrics" className="space-y-6">
          <div className="grid gap-6">
            {rubrics.map((rubric) => (
              <Card key={rubric.version} className="aulendur-hover-transform">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center space-x-2">
                        <span>{rubric.name}</span>
                        <Badge variant={rubric.status === 'active' ? 'default' : 'secondary'}>
                          {rubric.status}
                        </Badge>
                      </CardTitle>
                      <CardDescription>Version {rubric.version} • Created {rubric.created}</CardDescription>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="text-right mr-4">
                        <div className="text-lg font-bold">{rubric.accuracy}%</div>
                        <div className="text-xs text-muted-foreground">Accuracy</div>
                      </div>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </Button>
                      {rubric.status !== 'active' && (
                        <Button size="sm">
                          Activate
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <h4 className="font-semibold text-sm">Evaluation Categories</h4>
                    <div className="grid gap-3">
                      {rubric.categories.map((category, index) => (
                        <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                          <div>
                            <div className="font-medium text-sm">{category.name}</div>
                            <div className="text-xs text-muted-foreground">{category.description}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold">{category.weight}%</div>
                            <div className="text-xs text-muted-foreground">Weight</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
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
              <ScrollArea className="h-64">
                <div className="space-y-3">
                  {evaluationResults.map((result, index) => (
                    <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-background/50">
                      <div className="flex items-center space-x-4">
                        <div>
                          <div className="font-medium">{result.date}</div>
                          <div className="text-sm text-muted-foreground">{result.total} documents</div>
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
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Evaluations

