import { useState, useEffect } from 'react'
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
  XCircle,
  Loader2
} from 'lucide-react'
import { API_URL } from '@/config.js'

const Sources = () => {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch sources from API
  useEffect(() => {
    const fetchSources = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await fetch(`${API_URL}/api/v1/sources/`)
        if (!response.ok) throw new Error('Failed to fetch sources')
        const data = await response.json()
        const sourcesList = data.items || []

        // Enrich source data
        const enrichedSources = sourcesList.map(source => ({
          id: source.id,
          name: source.name,
          status: source.status.charAt(0).toUpperCase() + source.status.slice(1), // Capitalize
          lastRun: source.last_run ? formatTimeAgo(source.last_run) : 'Never',
          artifacts: source.document_count || 0,
          type: source.type.toUpperCase(),
          url: source.config?.start_urls?.[0] || 'N/A',
          schedule: source.schedule || 'Manual',
          health: 95 // Placeholder - no health tracking yet
        }))

        setSources(enrichedSources)
      } catch (err) {
        console.error('Error fetching sources:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchSources()
  }, [])

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now - date) / 1000)
    
    if (seconds < 60) return `${seconds} seconds ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading sources...</p>
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
              <span>Error Loading Sources</span>
            </CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

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

  const activeCount = sources.filter(s => s.status === 'Active').length
  const warningCount = sources.filter(s => s.status === 'Warning').length
  const pausedCount = sources.filter(s => s.status === 'Paused').length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sources<span className="placeholder-indicator">⭐</span></h1>
          <p className="text-muted-foreground">Manage data sources and monitoring</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Configure<span className="placeholder-indicator">⭐</span>
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Source<span className="placeholder-indicator">⭐</span>
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="aulendur-hover-transform relative">
          <span className="placeholder-card-indicator">⭐</span>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sources</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sources.length}</div>
            <p className="text-xs text-muted-foreground">Configured sources</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform relative">
          <span className="placeholder-card-indicator">⭐</span>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCount}</div>
            <p className="text-xs text-muted-foreground">Running normally</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform relative">
          <span className="placeholder-card-indicator">⭐</span>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Warnings</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{warningCount}</div>
            <p className="text-xs text-muted-foreground">Need attention</p>
          </CardContent>
        </Card>

        <Card className="aulendur-hover-transform relative">
          <span className="placeholder-card-indicator">⭐</span>
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
      <Card className="aulendur-gradient-card relative">
        <span className="placeholder-card-indicator">⭐</span>
        <CardHeader>
          <CardTitle>Source Management</CardTitle>
          <CardDescription>Monitor and configure your data sources</CardDescription>
        </CardHeader>
        <CardContent>
          {sources.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Globe className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No sources configured yet</p>
              <Button className="mt-4" variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Source<span className="placeholder-indicator">⭐</span>
              </Button>
            </div>
          ) : (
            <ScrollArea className="h-96">
              <div className="space-y-4">
                {sources.map((source) => (
                <Card key={source.id} className="aulendur-hover-transform relative">
                  <span className="placeholder-card-indicator">⭐</span>
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
                              <span>{source.artifacts} artifacts</span>
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
                            Resume<span className="placeholder-indicator">⭐</span>
                          </Button>
                        ) : (
                          <Button variant="outline" size="sm">
                            <Pause className="h-4 w-4 mr-2" />
                            Pause<span className="placeholder-indicator">⭐</span>
                          </Button>
                        )}
                        <Button variant="outline" size="sm">
                          <Settings className="h-4 w-4 mr-2" />
                          Configure<span className="placeholder-indicator">⭐</span>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default Sources

