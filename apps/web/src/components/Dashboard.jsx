import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
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
  BarChart3
} from 'lucide-react'

const Dashboard = () => {
  // Mock data for dashboard metrics
  const metrics = {
    totalArtifacts: 12847,
    todayProcessed: 1247,
    signalArtifacts: 892,
    activeSources: 47,
    evaluationAccuracy: 94.2,
    processingSpeed: 156
  }

  const recentActivity = [
    { type: "Signal", title: "NATO Strategic Assessment", time: "2 minutes ago", confidence: 92 },
    { type: "Review", title: "Economic Sanctions Analysis", time: "8 minutes ago", confidence: 87 },
    { type: "Signal", title: "Cybersecurity Threat Report", time: "15 minutes ago", confidence: 89 },
    { type: "Noise", title: "Social Media Post", time: "23 minutes ago", confidence: 23 }
  ]

  const sourceStatus = [
    { name: "NATO Strategic Communications", status: "active", docs: 1247, health: 98 },
    { name: "International Economic Forum", status: "active", docs: 892, health: 95 },
    { name: "Cybersecurity Research Institute", status: "active", docs: 634, health: 92 },
    { name: "Defense Policy Institute", status: "warning", docs: 445, health: 78 }
  ]

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

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing Speed</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.processingSpeed}</div>
            <p className="text-xs text-muted-foreground">
              Artifacts per hour
            </p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Load</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">67%</div>
            <Progress value={67} className="mt-2" />
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
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-background/50">
                  <div className="flex items-center space-x-3">
                    <Badge variant={activity.type === 'Signal' ? 'default' : activity.type === 'Review' ? 'secondary' : 'outline'}>
                      {activity.type}
                    </Badge>
                    <div>
                      <p className="text-sm font-medium">{activity.title}</p>
                      <p className="text-xs text-muted-foreground">{activity.time}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{activity.confidence}%</div>
                    <Progress value={activity.confidence} className="w-16 h-1" />
                  </div>
                </div>
              ))}
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

