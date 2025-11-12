import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog.jsx'
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
  Loader2,
  Trash2,
  Zap
} from 'lucide-react'
import { API_URL } from '@/config.js'
import { toast } from 'sonner'
import SourceFormModal from './SourceFormModal.jsx'

const Sources = () => {
  const [sources, setSources] = useState([])
  const [rawSources, setRawSources] = useState([]) // Store full source data
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [formModalOpen, setFormModalOpen] = useState(false)
  const [selectedSourceId, setSelectedSourceId] = useState(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState(null)
  const [updatingStatus, setUpdatingStatus] = useState(new Set())
  const [triggeringCrawl, setTriggeringCrawl] = useState(new Set())

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now - date) / 1000)
    
    if (seconds < 60) return `${seconds} seconds ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
  }

  // Fetch sources from API
  const fetchSources = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_URL}/api/v1/sources/`)
      if (!response.ok) throw new Error('Failed to fetch sources')
      const data = await response.json()
      const sourcesList = data.items || []

      // Store raw sources for editing
      setRawSources(sourcesList)

      // Enrich source data for display and fetch health
      const enrichedSourcesPromises = sourcesList
        .filter(source => source.status !== 'deleted') // Filter out deleted sources
        .map(async (source) => {
          // Fetch health data for each source
          let healthScore = 0
          let healthStatus = 'unknown'
          try {
            const healthResponse = await fetch(`${API_URL}/api/v1/sources/${source.id}/health`)
            if (healthResponse.ok) {
              const healthData = await healthResponse.json()
              healthScore = Math.round((healthData.health_score || 0) * 100)
              healthStatus = healthData.health_status || 'unknown'
            }
          } catch (err) {
            console.warn(`Failed to fetch health for source ${source.id}:`, err)
          }
          
          return {
            id: source.id,
            name: source.name,
            status: source.status.charAt(0).toUpperCase() + source.status.slice(1), // Capitalize
            statusRaw: source.status, // Keep raw status for API calls
            lastRun: source.last_run ? formatTimeAgo(source.last_run) : 'Never',
            artifacts: source.document_count || 0,
            type: source.type.toUpperCase(),
            url: source.config?.start_urls?.[0] || 'N/A',
            schedule: source.schedule || 'Manual',
            health: healthScore,
            healthStatus: healthStatus
          }
        })
      
      const enrichedSources = await Promise.all(enrichedSourcesPromises)

      setSources(enrichedSources)
    } catch (err) {
      console.error('Error fetching sources:', err)
      setError(err.message)
      toast.error('Failed to load sources')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSources()
  }, [])

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

  const handleAddSource = () => {
    setSelectedSourceId(null)
    setFormModalOpen(true)
  }

  const handleEditSource = (sourceId) => {
    setSelectedSourceId(sourceId)
    setFormModalOpen(true)
  }

  const handleFormSuccess = () => {
    fetchSources()
  }

  const updateSourceStatus = async (sourceId, newStatus) => {
    try {
      setUpdatingStatus(prev => new Set(prev).add(sourceId))
      
      const response = await fetch(`${API_URL}/api/v1/sources/${sourceId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to update status' }))
        throw new Error(errorData.detail || 'Failed to update status')
      }

      toast.success(`Source ${newStatus === 'paused' ? 'paused' : 'resumed'} successfully`)
      await fetchSources()
    } catch (err) {
      console.error('Error updating source status:', err)
      toast.error(err.message || 'Failed to update source status')
    } finally {
      setUpdatingStatus(prev => {
        const newSet = new Set(prev)
        newSet.delete(sourceId)
        return newSet
      })
    }
  }

  const handlePause = async (sourceId) => {
    await updateSourceStatus(sourceId, 'paused')
  }

  const handleResume = async (sourceId) => {
    await updateSourceStatus(sourceId, 'active')
  }

  const handleTriggerCrawl = async (sourceId) => {
    try {
      setTriggeringCrawl(prev => new Set(prev).add(sourceId))
      
      const response = await fetch(`${API_URL}/api/v1/sources/${sourceId}/trigger`, {
        method: 'POST',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to trigger crawl' }))
        throw new Error(errorData.detail || 'Failed to trigger crawl')
      }

      const result = await response.json()
      toast.success(`Crawl triggered successfully. Job ID: ${result.job_id}`)
      
      // Refresh sources to update last_run
      await fetchSources()
    } catch (err) {
      console.error('Error triggering crawl:', err)
      toast.error(err.message || 'Failed to trigger crawl')
    } finally {
      setTriggeringCrawl(prev => {
        const newSet = new Set(prev)
        newSet.delete(sourceId)
        return newSet
      })
    }
  }

  const handleDeleteClick = (sourceId) => {
    setDeleteTargetId(sourceId)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return

    try {
      const response = await fetch(`${API_URL}/api/v1/sources/${deleteTargetId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('Failed to delete source')
      }

      toast.success('Source deleted successfully')
      await fetchSources()
    } catch (err) {
      console.error('Error deleting source:', err)
      toast.error('Failed to delete source')
    } finally {
      setDeleteDialogOpen(false)
      setDeleteTargetId(null)
    }
  }

  const activeCount = sources.filter(s => s.statusRaw === 'active').length
  const warningCount = sources.filter(s => s.status === 'Warning').length
  const pausedCount = sources.filter(s => s.statusRaw === 'paused').length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sources</h1>
          <p className="text-muted-foreground">Manage data sources and monitoring</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button size="sm" onClick={handleAddSource}>
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
            <div className="text-2xl font-bold">{sources.length}</div>
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
          {sources.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Globe className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No sources configured yet</p>
              <Button className="mt-4" variant="outline" onClick={handleAddSource}>
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Source
              </Button>
            </div>
          ) : (
            <ScrollArea className="h-96">
              <div className="space-y-4">
                {sources.map((source) => (
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
                              <span>{source.artifacts} artifacts</span>
                              <span>•</span>
                              <span className="flex items-center space-x-1">
                                <span>Health:</span>
                                <Badge 
                                  variant={
                                    source.health >= 90 ? 'default' :
                                    source.health >= 70 ? 'secondary' :
                                    source.health >= 50 ? 'destructive' : 'destructive'
                                  }
                                  className={
                                    source.health >= 90 ? 'bg-green-500' :
                                    source.health >= 70 ? 'bg-yellow-500' :
                                    source.health >= 50 ? 'bg-orange-500' : 'bg-red-500'
                                  }
                                >
                                  {source.health}%
                                </Badge>
                              </span>
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
                        {source.statusRaw === 'paused' ? (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleResume(source.id)}
                            disabled={updatingStatus.has(source.id)}
                          >
                            {updatingStatus.has(source.id) ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <Play className="h-4 w-4 mr-2" />
                            )}
                            Resume
                          </Button>
                        ) : (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handlePause(source.id)}
                            disabled={updatingStatus.has(source.id)}
                          >
                            {updatingStatus.has(source.id) ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <Pause className="h-4 w-4 mr-2" />
                            )}
                            Pause
                          </Button>
                        )}
                        {source.statusRaw === 'active' && (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleTriggerCrawl(source.id)}
                            disabled={triggeringCrawl.has(source.id)}
                          >
                            {triggeringCrawl.has(source.id) ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <Zap className="h-4 w-4 mr-2" />
                            )}
                            Trigger
                          </Button>
                        )}
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleEditSource(source.id)}
                        >
                          <Settings className="h-4 w-4 mr-2" />
                          Configure
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleDeleteClick(source.id)}
                        >
                          <Trash2 className="h-4 w-4" />
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

      {/* Source Form Modal */}
      <SourceFormModal
        sourceId={selectedSourceId}
        open={formModalOpen}
        onOpenChange={setFormModalOpen}
        onSuccess={handleFormSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Source?</AlertDialogTitle>
            <AlertDialogDescription>
              This will mark the source as deleted. Artifacts collected from this source will remain in the system.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default Sources

