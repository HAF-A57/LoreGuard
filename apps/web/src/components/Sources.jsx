import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { 
  Globe, 
  Clock, 
  Database,
  Settings,
  Play,
  Pause,
  Plus,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react'

const Sources = () => {
  // Mock data for sources
  const mockSources = [
    { 
      id: 1,
      name: "NATO Strategic Communications Centre", 
      status: "Active", 
      lastRun: "2 hours ago", 
      documents: 1247,
      type: "RSS Feed",
      url: "https://stratcomcoe.org/feed",
      schedule: "Every 4 hours",
      health: 98
    },
    { 
      id: 2,
      name: "International Economic Forum", 
      status: "Active", 
      lastRun: "4 hours ago", 
      documents: 892,
      type: "Web Scraper",
      url: "https://ief.org/reports",
      schedule: "Daily at 06:00",
      health: 95
    },
    { 
      id: 3,
      name: "Cybersecurity Research Institute", 
      status: "Active", 
      lastRun: "6 hours ago", 
      documents: 634,
      type: "API",
      url: "https://api.cybersec-research.org",
      schedule: "Every 6 hours",
      health: 92
    },
    { 
      id: 4,
      name: "Defense Policy Institute", 
      status: "Warning", 
      lastRun: "2 days ago", 
      documents: 445,
      type: "RSS Feed",
      url: "https://defensepolicy.org/feed",
      schedule: "Every 8 hours",
      health: 78
    },
    { 
      id: 5,
      name: "Regional Security Council", 
      status: "Paused", 
      lastRun: "1 week ago", 
      documents: 234,
      type: "Web Scraper",
      url: "https://regsec.org/publications",
      schedule: "Daily at 12:00",
      health: 0
    }
  ]

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Active':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'Warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'Paused':
        return <Pause className="h-4 w-4 text-gray-500" />
      case 'Error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <CheckCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'RSS Feed':
        return <Globe className="h-4 w-4" />
      case 'API':
        return <Database className="h-4 w-4" />
      case 'Web Scraper':
        return <Globe className="h-4 w-4" />
      default:
        return <Globe className="h-4 w-4" />
    }
  }

  const activeCount = mockSources.filter(s => s.status === 'Active').length
  const warningCount = mockSources.filter(s => s.status === 'Warning').length
  const pausedCount = mockSources.filter(s => s.status === 'Paused').length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sources</h1>
          <p className="text-muted-foreground">Manage data sources and monitoring</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Source
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sources</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockSources.length}</div>
            <p className="text-xs text-muted-foreground">Configured sources</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCount}</div>
            <p className="text-xs text-muted-foreground">Running normally</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Warnings</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{warningCount}</div>
            <p className="text-xs text-muted-foreground">Need attention</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Paused</CardTitle>
            <Pause className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pausedCount}</div>
            <p className="text-xs text-muted-foreground">Temporarily disabled</p>
          </CardContent>
        </Card>
      </div>

      {/* Sources List */}
      <Card className="aulendur-gradient-card">
        <CardHeader>
          <CardTitle>Source Management</CardTitle>
          <CardDescription>Monitor and configure your data sources</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <div className="space-y-4">
              {mockSources.map((source) => (
                <Card key={source.id} className="aulendur-hover-transform">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          {getTypeIcon(source.type)}
                          {getStatusIcon(source.status)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <h3 className="font-semibold">{source.name}</h3>
                            <Badge variant={
                              source.status === 'Active' ? 'default' : 
                              source.status === 'Warning' ? 'destructive' : 'secondary'
                            }>
                              {source.status}
                            </Badge>
                          </div>
                          <div className="text-sm text-muted-foreground space-y-1">
                            <div className="flex items-center space-x-4">
                              <span>{source.type}</span>
                              <span>•</span>
                              <span>{source.documents} documents</span>
                              <span>•</span>
                              <span>Health: {source.health}%</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Clock className="h-3 w-3" />
                              <span>Last run: {source.lastRun}</span>
                              <span>•</span>
                              <span>Schedule: {source.schedule}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {source.status === 'Paused' ? (
                          <Button variant="outline" size="sm">
                            <Play className="h-4 w-4 mr-2" />
                            Resume
                          </Button>
                        ) : (
                          <Button variant="outline" size="sm">
                            <Pause className="h-4 w-4 mr-2" />
                            Pause
                          </Button>
                        )}
                        <Button variant="outline" size="sm">
                          <Settings className="h-4 w-4 mr-2" />
                          Configure
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

export default Sources

