/**
 * Component to display crawl status for a source
 * Shows progress bar, status badge, and real-time updates
 */

import { useEffect, useRef } from 'react'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Loader2, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'
import { useSourceCrawlStatus } from '@/lib/artifacts/hooks/useSourceCrawlStatus.js'
import { toast } from 'sonner'

const SourceCrawlStatus = ({ sourceId, sourceName, onStatusChange }) => {
  const { crawlStatus, hasActiveCrawl, latestJob, loading } = useSourceCrawlStatus(
    sourceId,
    true, // enabled
    3000 // poll every 3 seconds
  )
  
  const previousStatusRef = useRef(null)
  const previousProgressRef = useRef(null)

  // Track status changes and show toast notifications
  useEffect(() => {
    if (!latestJob) return

    const currentStatus = latestJob.status
    const previousStatus = previousStatusRef.current
    const currentProgress = latestJob.progress || 0
    const previousProgress = previousProgressRef.current || 0

    // Status change notifications
    if (previousStatus && previousStatus !== currentStatus) {
      if (currentStatus === 'completed') {
        toast.success(`Crawl completed for ${sourceName}`, {
          description: `Processed ${latestJob.items_processed || 0} artifacts`
        })
      } else if (currentStatus === 'failed') {
        toast.error(`Crawl failed for ${sourceName}`, {
          description: latestJob.error || 'Unknown error occurred'
        })
      } else if (currentStatus === 'running' && previousStatus === 'pending') {
        toast.info(`Crawl started for ${sourceName}`, {
          description: 'Processing artifacts...'
        })
      }
    }

    // Progress milestone notifications (every 25%)
    if (currentProgress > 0 && previousProgress !== currentProgress) {
      const progressMilestones = [25, 50, 75]
      const crossedMilestone = progressMilestones.find(
        milestone => previousProgress < milestone && currentProgress >= milestone
      )
      
      if (crossedMilestone) {
        toast.info(`Crawl progress: ${crossedMilestone}%`, {
          description: `${sourceName} - ${latestJob.items_processed || 0} artifacts processed`
        })
      }
    }

    previousStatusRef.current = currentStatus
    previousProgressRef.current = currentProgress

    // Notify parent component of status change
    if (onStatusChange && previousStatus !== currentStatus) {
      onStatusChange(currentStatus, latestJob)
    }
  }, [latestJob, sourceName, onStatusChange])

  // Don't render anything if no crawl status
  if (!crawlStatus || !hasActiveCrawl) {
    return null
  }

  const job = latestJob
  const status = job?.status || 'unknown'
  const progress = job?.progress || 0
  const itemsProcessed = job?.items_processed || 0
  const totalItems = job?.total_items || 0

  // Status badge configuration
  const getStatusConfig = () => {
    switch (status) {
      case 'running':
        return {
          label: 'Crawling',
          variant: 'default',
          icon: Loader2,
          className: 'bg-blue-500/20 text-blue-400 border-blue-500/50'
        }
      case 'pending':
        return {
          label: 'Pending',
          variant: 'secondary',
          icon: Clock,
          className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
        }
      case 'completed':
        return {
          label: 'Completed',
          variant: 'outline',
          icon: CheckCircle,
          className: 'bg-green-500/20 text-green-400 border-green-500/50'
        }
      case 'failed':
        return {
          label: 'Failed',
          variant: 'destructive',
          icon: XCircle,
          className: 'bg-red-500/20 text-red-400 border-red-500/50'
        }
      case 'hanging':
      case 'timeout':
        return {
          label: 'Hanging',
          variant: 'destructive',
          icon: AlertTriangle,
          className: 'bg-orange-500/20 text-orange-400 border-orange-500/50 animate-pulse'
        }
      default:
        return {
          label: status,
          variant: 'secondary',
          icon: Clock,
          className: ''
        }
    }
  }

  const statusConfig = getStatusConfig()
  const StatusIcon = statusConfig.icon

  return (
    <div className="mt-2 space-y-2">
      {/* Status Badge */}
      <div className="flex items-center space-x-2">
        <Badge 
          variant={statusConfig.variant}
          className={`${statusConfig.className} flex items-center space-x-1`}
        >
          {status === 'running' && <StatusIcon className="h-3 w-3 animate-spin" />}
          {status !== 'running' && <StatusIcon className="h-3 w-3" />}
          <span>{statusConfig.label}</span>
        </Badge>
        {status === 'running' && (
          <span className="text-xs text-muted-foreground">
            {itemsProcessed > 0 && totalItems > 0 
              ? `${itemsProcessed}/${totalItems} artifacts`
              : 'Processing...'}
          </span>
        )}
      </div>

      {/* Progress Bar */}
      {status === 'running' && (
        <div className="space-y-1">
          <Progress 
            value={progress} 
            className="h-2"
          />
          {progress > 0 && (
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{progress.toFixed(0)}% complete</span>
              {totalItems > 0 && (
                <span>{itemsProcessed} of {totalItems} artifacts</span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {status === 'failed' && job?.error && (
        <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-2">
          {job.error}
        </div>
      )}

      {/* Hanging Warning */}
      {(status === 'hanging' || status === 'timeout') && (
        <div className="text-xs text-orange-400 bg-orange-500/10 border border-orange-500/20 rounded p-2">
          Job appears to be hanging. Consider cancelling and retrying.
        </div>
      )}

      {/* Blocker Detection Alerts */}
      {job?.blocker_info && job.blocker_info.length > 0 && (
        <div className="space-y-2 mt-2">
          <div className="text-xs font-semibold text-muted-foreground flex items-center space-x-1">
            <AlertTriangle className="h-3 w-3 text-orange-500" />
            <span>Blockers Detected ({job.blocker_info.length})</span>
          </div>
          {job.blocker_info.slice(0, 3).map((blocker, idx) => {
            const severityColors = {
              critical: 'bg-red-500/10 border-red-500/30 text-red-400',
              high: 'bg-orange-500/10 border-orange-500/30 text-orange-400',
              medium: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
              low: 'bg-blue-500/10 border-blue-500/30 text-blue-400'
            }
            const severity = blocker.severity || 'medium'
            return (
              <div 
                key={idx}
                className={`text-xs p-2 border rounded ${severityColors[severity] || severityColors.medium}`}
              >
                <div className="font-semibold mb-1">{blocker.type.replace(/_/g, ' ').toUpperCase()}</div>
                <div className="text-xs opacity-90">{blocker.message}</div>
                {blocker.suggestions && blocker.suggestions.length > 0 && (
                  <div className="mt-1 text-xs opacity-75">
                    <div className="font-semibold mb-0.5">Suggestions:</div>
                    <ul className="list-disc list-inside space-y-0.5">
                      {blocker.suggestions.slice(0, 2).map((suggestion, sidx) => (
                        <li key={sidx}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )
          })}
          {job.blocker_info.length > 3 && (
            <div className="text-xs text-muted-foreground italic">
              +{job.blocker_info.length - 3} more blocker(s) detected
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SourceCrawlStatus

