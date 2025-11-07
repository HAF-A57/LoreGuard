import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
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
  Plus,
  Cpu,
  HardDrive,
  Timer,
  RefreshCw
} from 'lucide-react'
import { toast } from 'sonner'
import { API_URL } from '@/config.js'

const Jobs = () => {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedJobs, setSelectedJobs] = useState([])
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false)
  const [jobToCancel, setJobToCancel] = useState(null)
  const [healthSummary, setHealthSummary] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)

  // Fetch jobs from API
  const fetchJobs = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/jobs/?limit=1000`)
      if (response.ok) {
        const data = await response.json()
        setJobs(data.items || [])
        setLastUpdate(new Date())
      } else {
        console.error('Failed to fetch jobs:', response.statusText)
        toast.error('Failed to load jobs')
      }
    } catch (error) {
      console.error('Error fetching jobs:', error)
      toast.error('Error loading jobs')
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch active jobs with real-time monitoring
  const fetchActiveJobs = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/jobs/active/list`)
      if (response.ok) {
        const data = await response.json()
        // Update only active jobs, merge with full job list
        const activeJobIds = new Set(data.active_jobs.map(j => j.job_id))
        setJobs(prevJobs => {
          const updatedJobs = [...prevJobs]
          data.active_jobs.forEach(activeJob => {
            const index = updatedJobs.findIndex(j => j.id === activeJob.job_id)
            if (index >= 0) {
              // Merge active job data (with process info) into existing job
              updatedJobs[index] = { ...updatedJobs[index], ...activeJob }
            }
          })
          return updatedJobs
        })
        setLastUpdate(new Date())
      }
    } catch (error) {
      console.error('Error fetching active jobs:', error)
    }
  }, [])

  // Fetch health summary
  const fetchHealthSummary = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/jobs/health/summary`)
      if (response.ok) {
        const data = await response.json()
        setHealthSummary(data)
      }
    } catch (error) {
      console.error('Error fetching health summary:', error)
    }
  }, [])

  // Initial load
  useEffect(() => {
    fetchJobs()
    fetchHealthSummary()
  }, [fetchJobs, fetchHealthSummary])

  // Poll for active jobs every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchActiveJobs()
      fetchHealthSummary()
    }, 5000) // Poll every 5 seconds

    return () => clearInterval(interval)
  }, [fetchActiveJobs, fetchHealthSummary])

  // Cancel job handler
  const handleCancelJob = async (jobId, force = false) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/jobs/${jobId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ force })
      })

      if (response.ok) {
        const result = await response.json()
        toast.success(`Job cancelled: ${result.message}`)
        fetchJobs() // Refresh job list
        fetchActiveJobs()
      } else {
        const error = await response.json()
        toast.error(`Failed to cancel job: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error cancelling job:', error)
      toast.error(`Error cancelling job: ${error.message}`)
    } finally {
      setCancelDialogOpen(false)
      setJobToCancel(null)
    }
  }

  // Retry job handler
  const handleRetryJob = async (jobId) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/jobs/${jobId}/retry`, {
        method: 'POST'
      })

      if (response.ok) {
        const result = await response.json()
        toast.success(`Retry job created: ${result.new_job_id}`)
        fetchJobs() // Refresh job list
      } else {
        const error = await response.json()
        toast.error(`Failed to retry job: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error retrying job:', error)
      toast.error(`Error retrying job: ${error.message}`)
    }
  }

  // Format duration
  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A'
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    return `${Math.round(seconds / 3600)}h`
  }

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      return date.toLocaleString()
    } catch {
      return dateString
    }
  }

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
      case 'hanging':
      case 'timeout':
        return <AlertTriangle className="h-4 w-4 text-orange-500 animate-pulse" />
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'ingest':
        return <Database className="h-4 w-4" />
      case 'evaluate':
        return <Brain className="h-4 w-4" />
      case 'normalize':
        return <Activity className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const getTypeLabel = (type) => {
    const labels = {
      'ingest': 'Ingestion',
      'normalize': 'Normalization',
      'evaluate': 'Evaluation',
      'export': 'Export'
    }
    return labels[type] || type
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    )
  }

  const runningJobs = jobs.filter(job => job.status === 'running' || job.status === 'hanging')
  const completedJobs = jobs.filter(job => job.status === 'completed')
  const failedJobs = jobs.filter(job => job.status === 'failed' || job.status === 'timeout')
  const pendingJobs = jobs.filter(job => job.status === 'pending')
  const cancelledJobs = jobs.filter(job => job.status === 'cancelled')

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Jobs</h1>
          <p className="text-muted-foreground">
            Workflow monitoring and task management
            {lastUpdate && (
              <span className="ml-2 text-xs">
                Last updated: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={() => { fetchJobs(); fetchActiveJobs(); fetchHealthSummary(); }}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Health Summary */}
      {healthSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className={healthSummary.hanging_jobs > 0 ? 'border-orange-500' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Running</CardTitle>
              <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{healthSummary.running_jobs}</div>
              {healthSummary.hanging_jobs > 0 && (
                <p className="text-xs text-orange-500 mt-1">
                  {healthSummary.hanging_jobs} hanging
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
              <Clock className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{healthSummary.pending_jobs}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{healthSummary.completed_jobs}</div>
            </CardContent>
          </Card>

          <Card className={healthSummary.failed_jobs > 0 ? 'border-red-500' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
              <XCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{healthSummary.failed_jobs}</div>
              {healthSummary.recent_failures_24h > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  {healthSummary.recent_failures_24h} in last 24h
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="active" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="active">Active ({runningJobs.length})</TabsTrigger>
          <TabsTrigger value="pending">Pending ({pendingJobs.length})</TabsTrigger>
          <TabsTrigger value="completed">Completed ({completedJobs.length})</TabsTrigger>
          <TabsTrigger value="failed">Failed ({failedJobs.length})</TabsTrigger>
          <TabsTrigger value="cancelled">Cancelled ({cancelledJobs.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {runningJobs.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No active jobs
              </CardContent>
            </Card>
          ) : (
            runningJobs.map((job) => (
              <Card 
                key={job.id} 
                className={`aulendur-hover-transform ${
                  job.is_hanging ? 'border-orange-500 border-2' : ''
                }`}
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getTypeIcon(job.type)}
                      <div>
                        <CardTitle className="text-lg">
                          {getTypeLabel(job.type)} Job
                          {job.is_hanging && (
                            <Badge variant="outline" className="ml-2 border-orange-500 text-orange-500">
                              Hanging
                            </Badge>
                          )}
                        </CardTitle>
                        <CardDescription>Job ID: {job.id}</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(job.status)}
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          setJobToCancel(job)
                          setCancelDialogOpen(true)
                        }}
                      >
                        <Pause className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Progress */}
                    {job.progress !== undefined && (
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span>
                            {job.items_processed || 0}/{job.total_items || 0} items
                          </span>
                          <span>{job.progress || 0}%</span>
                        </div>
                        <Progress value={job.progress || 0} className="h-2" />
                      </div>
                    )}

                    {/* Process Information */}
                    {job.process_running && job.process_info && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-3 bg-muted rounded-lg">
                        <div className="flex items-center space-x-2">
                          <Cpu className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="text-xs text-muted-foreground">CPU</div>
                            <div className="text-sm font-medium">
                              {job.process_info.cpu_percent?.toFixed(1) || 'N/A'}%
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <HardDrive className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="text-xs text-muted-foreground">Memory</div>
                            <div className="text-sm font-medium">
                              {job.process_info.memory_mb ? `${job.process_info.memory_mb} MB` : 'N/A'}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Timer className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="text-xs text-muted-foreground">Runtime</div>
                            <div className="text-sm font-medium">
                              {formatDuration(job.process_info.runtime_seconds)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Activity className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="text-xs text-muted-foreground">PID</div>
                            <div className="text-sm font-medium font-mono">
                              {job.process_info.process_id || 'N/A'}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Hanging Warning */}
                    {job.is_hanging && (
                      <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                        <div className="text-sm text-orange-800">
                          <strong>Warning:</strong> {job.hanging_reason || 'Job appears to be hanging'}
                        </div>
                      </div>
                    )}

                    {/* Timeline */}
                    {job.timeline && job.timeline.length > 0 && (
                      <div className="text-sm space-y-1">
                        <div className="text-muted-foreground mb-2">Timeline:</div>
                        <ScrollArea className="h-24">
                          {job.timeline.slice(-5).map((entry, idx) => (
                            <div key={idx} className="text-xs">
                              <span className="text-muted-foreground">
                                {formatDate(entry.timestamp)}:
                              </span>{' '}
                              <span className="font-medium">{entry.status}</span>
                              {entry.message && <span className="text-muted-foreground"> - {entry.message}</span>}
                            </div>
                          ))}
                        </ScrollArea>
                      </div>
                    )}

                    {/* Duration */}
                    {job.duration_seconds && (
                      <div className="text-sm text-muted-foreground">
                        Duration: {formatDuration(job.duration_seconds)}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="pending" className="space-y-4">
          {pendingJobs.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No pending jobs
              </CardContent>
            </Card>
          ) : (
            pendingJobs.map((job) => (
              <Card key={job.id} className="aulendur-hover-transform">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getTypeIcon(job.type)}
                      <div>
                        <CardTitle className="text-lg">{getTypeLabel(job.type)} Job</CardTitle>
                        <CardDescription>Job ID: {job.id}</CardDescription>
                      </div>
                    </div>
                    {getStatusIcon(job.status)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-muted-foreground">
                    Created: {formatDate(job.created_at)}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          {completedJobs.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No completed jobs
              </CardContent>
            </Card>
          ) : (
            completedJobs.slice(0, 50).map((job) => (
              <Card key={job.id} className="aulendur-hover-transform">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getTypeIcon(job.type)}
                      <div>
                        <CardTitle className="text-lg">{getTypeLabel(job.type)} Job</CardTitle>
                        <CardDescription>Job ID: {job.id}</CardDescription>
                      </div>
                    </div>
                    {getStatusIcon(job.status)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Started:</span>
                      <span className="ml-2">{formatDate(job.created_at)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Completed:</span>
                      <span className="ml-2">{formatDate(job.updated_at)}</span>
                    </div>
                    {job.duration_seconds && (
                      <div>
                        <span className="text-muted-foreground">Duration:</span>
                        <span className="ml-2">{formatDuration(job.duration_seconds)}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="failed" className="space-y-4">
          {failedJobs.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No failed jobs
              </CardContent>
            </Card>
          ) : (
            failedJobs.map((job) => (
              <Card key={job.id} className="aulendur-hover-transform border-red-200">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getTypeIcon(job.type)}
                      <div>
                        <CardTitle className="text-lg">{getTypeLabel(job.type)} Job</CardTitle>
                        <CardDescription>Job ID: {job.id}</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(job.status)}
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleRetryJob(job.id)}
                      >
                        <RotateCcw className="h-4 w-4 mr-2" />
                        Retry
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {job.error && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <div className="text-sm text-red-800">
                          <strong>Error:</strong> {job.error}
                        </div>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Started:</span>
                        <span className="ml-2">{formatDate(job.created_at)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Failed:</span>
                        <span className="ml-2">{formatDate(job.updated_at)}</span>
                      </div>
                      {job.retries > 0 && (
                        <div>
                          <span className="text-muted-foreground">Retries:</span>
                          <span className="ml-2">{job.retries}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="cancelled" className="space-y-4">
          {cancelledJobs.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No cancelled jobs
              </CardContent>
            </Card>
          ) : (
            cancelledJobs.slice(0, 50).map((job) => (
              <Card key={job.id} className="aulendur-hover-transform">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getTypeIcon(job.type)}
                      <div>
                        <CardTitle className="text-lg">{getTypeLabel(job.type)} Job</CardTitle>
                        <CardDescription>Job ID: {job.id}</CardDescription>
                      </div>
                    </div>
                    {getStatusIcon(job.status)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-muted-foreground">
                    Cancelled: {formatDate(job.updated_at)}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Cancel Job Dialog */}
      <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Job</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel this job? 
              {jobToCancel?.process_running && (
                <span className="block mt-2 text-orange-600">
                  The running process will be terminated.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep Running</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => jobToCancel && handleCancelJob(jobToCancel.id, false)}
            >
              Cancel Gracefully
            </AlertDialogAction>
            {jobToCancel?.process_running && (
              <AlertDialogAction
                onClick={() => jobToCancel && handleCancelJob(jobToCancel.id, true)}
                className="bg-red-600 hover:bg-red-700"
              >
                Force Kill
              </AlertDialogAction>
            )}
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default Jobs
