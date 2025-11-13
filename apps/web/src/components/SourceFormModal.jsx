import { useState, useEffect } from 'react'
import { API_URL } from '@/config.js'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Loader2 } from 'lucide-react'
import SourceConfigForm from './SourceConfigForm.jsx'
import ScheduleSelector from './ScheduleSelector.jsx'
import InfoTooltip from './InfoTooltip.jsx'

const SourceFormModal = ({ sourceId, open, onOpenChange, onSuccess }) => {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  
  const [formData, setFormData] = useState({
    name: '',
    type: 'web',
    status: 'active',
    schedule: '',
    tags: [],
    config: {
      start_urls: [],
      crawl_scope: {
        max_depth: 3,
        max_artifacts: 0
      },
      filtering: {
        allowed_domains: []
      }
    }
  })

  const isEditMode = !!sourceId

  // Load source data when editing
  useEffect(() => {
    if (open && isEditMode && sourceId) {
      fetchSource()
    } else if (open && !isEditMode) {
      // Reset form for new source
      setFormData({
        name: '',
        type: 'web',
        status: 'active',
        schedule: '',
        tags: [],
        config: {
          start_urls: [],
          crawl_scope: {
            max_depth: 3,
            max_artifacts: 0
          },
          filtering: {
            allowed_domains: []
          },
          extraction: {
            extract_documents: true,
            extract_pdfs: true,
            max_document_size_mb: 50
          },
          compliance: {
            obey_robots_txt: true,
            robots_txt_user_agent: '*',
            robots_txt_warning_only: false,
            detect_blockers: true,
            notify_on_blocker: true,
            blocker_response_strategy: 'notify',
            handle_403: 'retry',
            handle_429: 'retry',
            handle_cloudflare: 'notify',
            handle_captcha: 'pause',
            allow_proxy_bypass: false,
            allow_browser_bypass: false,
            allow_user_agent_rotation: true
          }
        }
      })
      setError(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, sourceId, isEditMode])

  const fetchSource = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_URL}/api/v1/sources/${sourceId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch source')
      }
      const source = await response.json()
      
      // Merge config with defaults to ensure all fields are present
      const defaultConfig = {
        start_urls: [],
        crawl_scope: { max_depth: 3, max_artifacts: 0 },
        filtering: { allowed_domains: [] },
        extraction: {
          extract_documents: true,
          extract_pdfs: true,
          max_document_size_mb: 50
        },
        compliance: {
          obey_robots_txt: true,
          robots_txt_user_agent: '*',
          robots_txt_warning_only: false,
          detect_blockers: true,
          notify_on_blocker: true,
          blocker_response_strategy: 'notify',
          handle_403: 'retry',
          handle_429: 'retry',
          handle_cloudflare: 'notify',
          handle_captcha: 'pause',
          allow_proxy_bypass: false,
          allow_browser_bypass: false,
          allow_user_agent_rotation: true
        }
      }
      
      const sourceConfig = source.config || {}
      const mergedConfig = {
        ...defaultConfig,
        ...sourceConfig,
        crawl_scope: { ...defaultConfig.crawl_scope, ...(sourceConfig.crawl_scope || {}) },
        filtering: { ...defaultConfig.filtering, ...(sourceConfig.filtering || {}) },
        extraction: { ...defaultConfig.extraction, ...(sourceConfig.extraction || {}) },
        compliance: { ...defaultConfig.compliance, ...(sourceConfig.compliance || {}) }
      }
      
      setFormData({
        name: source.name || '',
        type: source.type || 'web',
        status: source.status || 'active',
        schedule: source.schedule || '',
        tags: source.tags || [],
        config: mergedConfig
      })
    } catch (err) {
      console.error('Error fetching source:', err)
      setError(err.message)
      toast.error('Failed to load source')
    } finally {
      setLoading(false)
    }
  }

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('Source name is required')
      return false
    }
    
    if (!formData.config.start_urls || formData.config.start_urls.length === 0) {
      setError('At least one start URL is required')
      return false
    }
    
    // Validate URLs
    for (const url of formData.config.start_urls) {
      try {
        new URL(url)
      } catch {
        setError(`Invalid URL: ${url}`)
        return false
      }
    }
    
    // Validate domains
    for (const domain of formData.config.filtering.allowed_domains || []) {
      if (!domain.match(/^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/)) {
        setError(`Invalid domain format: ${domain}`)
        return false
      }
    }
    
    setError(null)
    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    try {
      setSaving(true)
      setError(null)

      const payload = {
        name: formData.name.trim(),
        type: formData.type,
        status: formData.status,
        schedule: formData.schedule || null,
        tags: formData.tags,
        config: formData.config
      }

      const url = isEditMode 
        ? `${API_URL}/api/v1/sources/${sourceId}`
        : `${API_URL}/api/v1/sources/`
      
      const method = isEditMode ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Failed to ${isEditMode ? 'update' : 'create'} source`)
      }

      toast.success(`Source ${isEditMode ? 'updated' : 'created'} successfully`)
      
      if (onSuccess) {
        onSuccess()
      }
      
      onOpenChange(false)
    } catch (err) {
      console.error('Error saving source:', err)
      setError(err.message)
      toast.error(err.message || `Failed to ${isEditMode ? 'update' : 'create'} source`)
    } finally {
      setSaving(false)
    }
  }

  const handleConfigChange = (newConfig) => {
    setFormData(prev => ({
      ...prev,
      config: newConfig
    }))
  }

  const handleTagInput = (e) => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      e.preventDefault()
      const tag = e.target.value.trim()
      if (!formData.tags.includes(tag)) {
        setFormData(prev => ({
          ...prev,
          tags: [...prev.tags, tag]
        }))
        e.target.value = ''
      }
    }
  }

  const removeTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 flex-shrink-0">
          <DialogTitle>{isEditMode ? 'Edit Source' : 'Create New Source'}</DialogTitle>
          <DialogDescription>
            {isEditMode 
              ? 'Update source configuration and settings'
              : 'Configure a new data source for artifact collection'
            }
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8 px-6">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <>
            <ScrollArea className="flex-1 min-h-0 px-6">
              <form id="source-form" onSubmit={handleSubmit} className="space-y-6 py-4">
            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Basic Information */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Source Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Brookings Institution"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="type">Source Type *</Label>
                  <Select
                    value={formData.type}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, type: value }))}
                  >
                    <SelectTrigger id="type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="web">Web</SelectItem>
                      <SelectItem value="api">API</SelectItem>
                      <SelectItem value="feed">Feed</SelectItem>
                      <SelectItem value="rss">RSS</SelectItem>
                      <SelectItem value="twitter">Twitter</SelectItem>
                      <SelectItem value="reddit">Reddit</SelectItem>
                      <SelectItem value="news">News</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="status">Status *</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, status: value }))}
                  >
                    <SelectTrigger id="status">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="paused">Paused</SelectItem>
                      <SelectItem value="error">Error</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <ScheduleSelector
                value={formData.schedule}
                onChange={(schedule) => setFormData(prev => ({ ...prev, schedule }))}
              />

              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <Label htmlFor="tags">Tags</Label>
                  <InfoTooltip content="Tags help you organize and categorize your sources. You can use tags to filter sources, group related sources together, or add metadata for easier searching and management. For example, you might tag sources by topic (e.g., 'china', 'economics'), by organization (e.g., 'brookings', 'rand'), or by content type (e.g., 'research', 'news'). Press Enter after typing each tag to add it." />
                </div>
                <Input
                  id="tags"
                  placeholder="Press Enter to add a tag"
                  onKeyDown={handleTagInput}
                />
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2 py-1 rounded-md bg-secondary text-secondary-foreground text-sm"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="ml-2 hover:text-destructive"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <Separator />

            {/* Configuration Section */}
            <div className="space-y-4">
              <h3 className="font-semibold text-base">Crawl Configuration</h3>
              <SourceConfigForm
                config={formData.config}
                onChange={handleConfigChange}
              />
            </div>
              </form>
            </ScrollArea>

            <DialogFooter className="px-6 pb-6 pt-4 flex-shrink-0 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                form="source-form"
                disabled={saving}
              >
                {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {isEditMode ? 'Update Source' : 'Create Source'}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default SourceFormModal

