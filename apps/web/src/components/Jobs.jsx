import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Trash2, 
  Clock, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  Loader2,
  Activity,
  Database,
  Brain,
  Globe,
  Settings,
  Plus
} from 'lucide-react'

const Jobs = () => {
  const [selectedJobs, setSelectedJobs] = useState([])

  // Mock data for jobs
  const jobs = [
    {
      id: 1,
      name: "NATO Sources Ingestion",
      type: "ingestion",
      status: "running",
      progress: 67,
      startTime: "2024-09-10 14:30:00",
      estimatedCompletion: "2024-09-10 15:45:00",
      artifactsProcessed: 1247,
      totalArtifacts: 1850,
      source: "NATO Strategic Communications Centre",
      priority: "high"
    },
    {
      id: 2,
      name: "Artifact Evaluation Batch",
      type: "evaluation",
      status: "running",
      progress: 23,
      startTime: "2024-09-10 14:15:00",
      estimatedCompletion: "2024-09-10 16:20:00",
      artifactsProcessed: 89,
      totalArtifacts: 387,
      source: "Multiple Sources",
      priority: "normal"
    },
    {
      id: 3,
      name: "Economic Forum Crawl",
      type: "crawling",
      status: "completed",
      progress: 100,
      startTime: "2024-09-10 13:00:00",
      completionTime: "2024-09-10 13:45:00",
      artifactsProcessed: 156,
      totalArtifacts: 156,
      source: "International Economic Forum",
      priority: "normal"
    },
    {
      id: 4,
      name: "Cybersecurity Reports Processing",
      type: "processing",
      status: "failed",
      progress: 45,
      startTime: "2024-09-10 12:30:00",
      failureTime: "2024-09-10 13:15:00",
      artifactsProcessed: 67,
      totalArtifacts: 149,
      source: "Cybersecurity Research Institute",
      priority: "normal",
      error: "Connection timeout to source API"
    },
    {
      id: 5,
      name: "Library Export Generation",
      type: "export",
      status: "pending",
      progress: 0,
      scheduledTime: "2024-09-10 16:00:00",
      artifactsProcessed: 0,
      totalArtifacts: 23,
      source: "Signal Library",
      priority: "low"
    }
  ]

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'ingestion':
        return <Database className="h-4 w-4" />
      case 'evaluation':
        return <Brain className="h-4 w-4" />
      case 'crawling':
        return <Globe className="h-4 w-4" />
      case 'processing':
        return <Activity className="h-4 w-4" />
      case 'export':
        return <Settings className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const runningJobs = jobs.filter(job => job.status === 'running')
  const completedJobs = jobs.filter(job => job.status === 'completed')
  const failedJobs = jobs.filter(job => job.status === 'failed')
  const pendingJobs = jobs.filter(job => job.status === 'pending')

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Jobs</h1>
          <p className="text-muted-foreground">Workflow monitoring and task management</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Queue Settings
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Job
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{runningJobs.length}</div>
            <p className="text-xs text-muted-foreground">Active jobs</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingJobs.length}</div>
            <p className="text-xs text-muted-foreground">Queued jobs</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedJobs.length}</div>
            <p className="text-xs text-muted-foreground">Today</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{failedJobs.length}</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="active" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="active">Active ({runningJobs.length})</TabsTrigger>
          <TabsTrigger value="pending">Pending ({pendingJobs.length})</TabsTrigger>
          <TabsTrigger value="completed">Completed ({completedJobs.length})</TabsTrigger>
          <TabsTrigger value="failed">Failed ({failedJobs.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {runningJobs.map((job) => (
            <Card key={job.id} className="aulendur-hover-transform">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getTypeIcon(job.type)}
                    <div>
                      <CardTitle className="text-lg">{job.name}</CardTitle>
                      <CardDescription>{job.source}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={job.priority === 'high' ? 'destructive' : job.priority === 'normal' ? 'default' : 'secondary'}>
                      {job.priority} priority
                    </Badge>
                    {getStatusIcon(job.status)}
                    <Button variant="outline" size="sm">
                      <Pause className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Progress: {job.artifactsProcessed}/{job.totalArtifacts} artifacts</span>
                      <span>{job.progress}%</span>
                    </div>
                    <Progress value={job.progress} className="h-2" />
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Started:</span>
                      <span className="ml-2">{job.startTime}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Est. Completion:</span>
                      <span className="ml-2">{job.estimatedCompletion}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="pending" className="space-y-4">
          {pendingJobs.map((job) => (
            <Card key={job.id} className="aulendur-hover-transform">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getTypeIcon(job.type)}
                    <div>
                      <CardTitle className="text-lg">{job.name}</CardTitle>
                      <CardDescription>{job.source}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={job.priority === 'high' ? 'destructive' : job.priority === 'normal' ? 'default' : 'secondary'}>
                      {job.priority} priority
                    </Badge>
                    {getStatusIcon(job.status)}
                    <Button variant="outline" size="sm">
                      <Play className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-sm">
                  <span className="text-muted-foreground">Scheduled:</span>
                  <span className="ml-2">{job.scheduledTime}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          {completedJobs.map((job) => (
            <Card key={job.id} className="aulendur-hover-transform">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getTypeIcon(job.type)}
                    <div>
                      <CardTitle className="text-lg">{job.name}</CardTitle>
                      <CardDescription>{job.source}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(job.status)}
                    <span className="text-sm text-muted-foreground">
                      {job.artifactsProcessed} artifacts processed
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Started:</span>
                    <span className="ml-2">{job.startTime}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Completed:</span>
                    <span className="ml-2">{job.completionTime}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="failed" className="space-y-4">
          {failedJobs.map((job) => (
            <Card key={job.id} className="aulendur-hover-transform border-red-200">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getTypeIcon(job.type)}
                    <div>
                      <CardTitle className="text-lg">{job.name}</CardTitle>
                      <CardDescription>{job.source}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(job.status)}
                    <Button variant="outline" size="sm">
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="text-sm text-red-800">
                      <strong>Error:</strong> {job.error}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Started:</span>
                      <span className="ml-2">{job.startTime}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Failed:</span>
                      <span className="ml-2">{job.failureTime}</span>
                    </div>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">Progress when failed:</span>
                    <span className="ml-2">{job.artifactsProcessed}/{job.totalArtifacts} artifacts ({job.progress}%)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Jobs

