import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Switch } from '@/components/ui/switch.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { 
  Settings as SettingsIcon, 
  Brain, 
  Database, 
  Bell, 
  Users, 
  Shield,
  Key,
  Globe,
  Zap,
  Save,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Edit,
  Trash2,
  Plus,
  Loader2,
  PlayCircle
} from 'lucide-react'
import { API_URL } from '@/config.js'
import { toast } from 'sonner'
import PromptTemplates from './PromptTemplates.jsx'

const Settings = () => {
  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    systemHealth: true,
    jobFailures: true,
    weeklyReports: false
  })

  const [systemSettings, setSystemSettings] = useState({
    autoEvaluation: true,
    batchProcessing: true,
    realTimeIngestion: false,
    debugMode: false
  })

  // LLM Providers state
  const [llmProviders, setLlmProviders] = useState([])
  const [loadingProviders, setLoadingProviders] = useState(true)
  const [showProviderDialog, setShowProviderDialog] = useState(false)
  const [editingProvider, setEditingProvider] = useState(null)
  const [providerForm, setProviderForm] = useState({
    name: '',
    provider: 'openai',
    model: '',
    api_key: '',
    base_url: '',
    status: 'inactive',
    priority: 'normal',
    is_default: false,
    description: ''
  })
  const [availableModels, setAvailableModels] = useState([])
  const [detectingModels, setDetectingModels] = useState(false)
  const [modelDetectionError, setModelDetectionError] = useState(null)
  const [testingProvider, setTestingProvider] = useState(null)
  const [testResult, setTestResult] = useState(null)

  // Fetch LLM providers from API
  useEffect(() => {
    fetchProviders()
  }, [])

  const fetchProviders = async () => {
    try {
      setLoadingProviders(true)
      // Add timeout to prevent infinite spinning
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const response = await fetch(`${API_URL}/api/v1/llm-providers/`, {
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (response.ok) {
        const data = await response.json()
        setLlmProviders(data.items || [])
      } else {
        console.error('Failed to fetch LLM providers:', response.statusText)
        toast.error(`Failed to load providers: ${response.statusText}`)
        setLlmProviders([])
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error('Request timeout fetching LLM providers')
        toast.error('Request timed out. The API may be slow or unresponsive.')
      } else {
        console.error('Error fetching LLM providers:', error)
        toast.error(`Error loading providers: ${error.message}`)
      }
      setLlmProviders([])
    } finally {
      setLoadingProviders(false)
    }
  }

  const handleAddProvider = () => {
    setEditingProvider(null)
    setProviderForm({
      name: '',
      provider: 'openai',
      model: '',
      api_key: '',
      base_url: '',
      status: 'inactive',
      priority: 'normal',
      is_default: false,
      description: ''
    })
    setAvailableModels([])
    setModelDetectionError(null)
    setShowProviderDialog(true)
  }

  const handleEditProvider = (provider) => {
    setEditingProvider(provider)
    setProviderForm({
      name: provider.name,
      provider: provider.provider,
      model: provider.model,
      api_key: '', // Don't pre-fill API key for security
      base_url: provider.base_url || '',
      status: provider.status,
      priority: provider.priority,
      is_default: provider.is_default,
      description: provider.description || ''
    })
    setAvailableModels([])
    setModelDetectionError(null)
    setShowProviderDialog(true)
  }

  const detectModels = async () => {
    if (!providerForm.api_key || !providerForm.provider) {
      setModelDetectionError('Please enter an API key and select a provider')
      return
    }

    try {
      setDetectingModels(true)
      setModelDetectionError(null)
      
      const requestBody = {
        provider: providerForm.provider,
        api_key: providerForm.api_key,
        ...(providerForm.base_url && { base_url: providerForm.base_url })
      }
      
      const url = `${API_URL}/api/v1/llm-providers/detect-models`
      console.log('Detecting models:', { 
        provider: providerForm.provider, 
        url,
        hasApiKey: !!providerForm.api_key,
        hasBaseUrl: !!providerForm.base_url
      })
      
      // Add timeout to prevent infinite spinning
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 45000) // 45 second timeout for model detection
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      console.log('Model detection response:', { 
        status: response.status, 
        ok: response.ok,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Model detection success:', { 
          count: data.count, 
          models: data.models?.length,
          provider: data.provider
        })
        setAvailableModels(data.models || [])
        
        // Auto-select first model if none selected
        if (!providerForm.model && data.models && data.models.length > 0) {
          setProviderForm({ ...providerForm, model: data.models[0].id })
        }
      } else {
        let errorDetail = 'Failed to detect models'
        try {
          const errorText = await response.text()
          console.error('Model detection error response text:', errorText)
          try {
            const error = JSON.parse(errorText)
            errorDetail = error.detail || error.message || errorDetail
            console.error('Model detection error response:', error)
          } catch (parseError) {
            errorDetail = errorText || `HTTP ${response.status}: ${response.statusText}`
          }
        } catch (e) {
          errorDetail = `HTTP ${response.status}: ${response.statusText}`
          console.error('Model detection error - could not parse response:', e)
        }
        setModelDetectionError(errorDetail)
        setAvailableModels([])
      }
    } catch (error) {
      console.error('Error detecting models:', error)
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      })
      
      if (error.name === 'AbortError') {
        setModelDetectionError('Request timed out. The API may be slow or unresponsive. Please try again.')
        toast.error('Model detection timed out. Please check your API key and try again.')
      } else {
        setModelDetectionError(`Error: ${error.message || 'Network error occurred'}`)
        toast.error(`Model detection failed: ${error.message || 'Unknown error'}`)
      }
      setAvailableModels([])
    } finally {
      setDetectingModels(false)
    }
  }

  const handleSaveProvider = async () => {
    try {
      const url = editingProvider 
        ? `${API_URL}/api/v1/llm-providers/${editingProvider.id}`  // No trailing slash for PUT (path parameter)
        : `${API_URL}/api/v1/llm-providers/`  // Trailing slash for POST (list route)
      
      const method = editingProvider ? 'PUT' : 'POST'
      
      // Prepare form data - exclude empty API key when editing (don't overwrite existing key)
      const formData = { ...providerForm }
      if (editingProvider && !formData.api_key) {
        delete formData.api_key  // Don't send empty API key on update
      }
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        setShowProviderDialog(false)
        fetchProviders() // Refresh list
      } else {
        const error = await response.json()
        alert(`Failed to save provider: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error saving provider:', error)
      alert(`Error saving provider: ${error.message}`)
    }
  }

  const handleDeleteProvider = async (providerId) => {
    if (!confirm('Are you sure you want to delete this LLM provider?')) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/api/v1/llm-providers/${providerId}`, {  // No trailing slash for DELETE (path parameter)
        method: 'DELETE'
      })

      if (response.ok) {
        fetchProviders() // Refresh list
      } else {
        const error = await response.json()
        alert(`Failed to delete provider: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error deleting provider:', error)
      alert(`Error deleting provider: ${error.message}`)
    }
  }

  const handleTestProvider = async (providerId) => {
    try {
      setTestingProvider(providerId)
      setTestResult(null)
      
      const response = await fetch(`${API_URL}/api/v1/llm-providers/${providerId}/test`, {
        method: 'POST'
      })
      
      const result = await response.json()
      setTestResult(result)
      
      // Auto-clear result after 10 seconds
      setTimeout(() => {
        setTestResult(null)
      }, 10000)
    } catch (error) {
      console.error('Error testing provider:', error)
      setTestResult({
        success: false,
        error: `Test failed: ${error.message}`,
        error_code: 500
      })
    } finally {
      setTestingProvider(null)
    }
  }

  const handleStatusChange = async (providerId, newStatus) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/llm-providers/${providerId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
      })

      if (response.ok) {
        fetchProviders() // Refresh list
      } else {
        const error = await response.json()
        alert(`Failed to update status: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error updating status:', error)
      alert(`Error updating status: ${error.message}`)
    }
  }

  const capitalizeStatus = (status) => {
    if (!status) return status
    return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
  }

  // Mock data for users
  const users = [
    {
      id: 1,
      name: "John Smith",
      email: "john.smith@aulendur.com",
      role: "Administrator",
      status: "active",
      lastLogin: "2024-09-10 14:30:00"
    },
    {
      id: 2,
      name: "Sarah Johnson",
      email: "sarah.johnson@aulendur.com",
      role: "Analyst",
      status: "active",
      lastLogin: "2024-09-10 13:45:00"
    },
    {
      id: 3,
      name: "Mike Wilson",
      email: "mike.wilson@aulendur.com",
      role: "Operator",
      status: "inactive",
      lastLogin: "2024-09-08 16:20:00"
    }
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">System configuration and preferences</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset to Defaults
          </Button>
          <Button size="sm">
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>

      <Tabs defaultValue="system" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="models">AI Models</TabsTrigger>
          <TabsTrigger value="prompts">Prompts</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="space-y-6">
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <SettingsIcon className="h-5 w-5" />
                <span>System Configuration</span>
              </CardTitle>
              <CardDescription>Core system settings and processing options</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Automatic Evaluation</div>
                    <div className="text-xs text-muted-foreground">
                      Automatically evaluate new artifacts using active rubric
                    </div>
                  </div>
                  <Switch
                    checked={systemSettings.autoEvaluation}
                    onCheckedChange={(checked) => 
                      setSystemSettings(prev => ({ ...prev, autoEvaluation: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Batch Processing</div>
                    <div className="text-xs text-muted-foreground">
                      Process artifacts in batches for improved efficiency
                    </div>
                  </div>
                  <Switch
                    checked={systemSettings.batchProcessing}
                    onCheckedChange={(checked) => 
                      setSystemSettings(prev => ({ ...prev, batchProcessing: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Real-time Ingestion</div>
                    <div className="text-xs text-muted-foreground">
                      Process artifacts immediately as they are discovered
                    </div>
                  </div>
                  <Switch
                    checked={systemSettings.realTimeIngestion}
                    onCheckedChange={(checked) => 
                      setSystemSettings(prev => ({ ...prev, realTimeIngestion: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Debug Mode</div>
                    <div className="text-xs text-muted-foreground">
                      Enable detailed logging and debugging information
                    </div>
                  </div>
                  <Switch
                    checked={systemSettings.debugMode}
                    onCheckedChange={(checked) => 
                      setSystemSettings(prev => ({ ...prev, debugMode: checked }))
                    }
                  />
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Processing Batch Size</label>
                  <Input type="number" defaultValue="50" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Evaluation Timeout (seconds)</label>
                  <Input type="number" defaultValue="30" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Concurrent Jobs</label>
                  <Input type="number" defaultValue="5" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Retry Attempts</label>
                  <Input type="number" defaultValue="3" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-6">
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <Brain className="h-5 w-5" />
                    <span>AI Model Configuration</span>
                  </CardTitle>
                  <CardDescription>Manage LLM models for artifact evaluation</CardDescription>
                </div>
                <Button onClick={handleAddProvider} size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Provider
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loadingProviders ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">Loading providers...</span>
                </div>
              ) : llmProviders.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">No LLM providers configured</p>
                  <Button onClick={handleAddProvider} variant="outline">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Your First Provider
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {llmProviders.map((provider) => (
                    <Card 
                      key={provider.id} 
                      className={`aulendur-hover-transform ${
                        provider.is_default 
                          ? 'border-2 border-primary shadow-lg bg-primary/5 dark:bg-primary/10' 
                          : ''
                      }`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div>
                              <div className="font-medium flex items-center space-x-2 flex-wrap gap-2">
                                <span>{provider.name}</span>
                                {provider.is_default && (
                                  <Badge variant="default" className="font-semibold">Default</Badge>
                                )}
                                <Select
                                  value={provider.status}
                                  onValueChange={(newStatus) => handleStatusChange(provider.id, newStatus)}
                                >
                                  <SelectTrigger className="h-auto w-auto p-0 border-0 bg-transparent hover:bg-transparent shadow-none focus:ring-0 focus-visible:ring-0 data-[state=open]:bg-transparent [&>svg]:opacity-50 [&>svg]:hover:opacity-70">
                                    <SelectValue>
                                      <Badge 
                                        variant={
                                          provider.status === 'active' ? 'default' : 
                                          provider.status === 'backup' ? 'secondary' : 'outline'
                                        }
                                        className="cursor-pointer hover:opacity-80 transition-opacity"
                                      >
                                        {capitalizeStatus(provider.status)}
                                      </Badge>
                                    </SelectValue>
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="active">Active</SelectItem>
                                    <SelectItem value="backup">Backup</SelectItem>
                                    <SelectItem value="inactive">Inactive</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div className="text-sm text-muted-foreground">
                                {provider.provider} • {provider.model}
                                {provider.description && ` • ${provider.description}`}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {provider.cost_per_token && (
                              <div className="text-right text-sm mr-2">
                                <div>${provider.cost_per_token}/token</div>
                                {provider.avg_response_time && (
                                  <div className="text-muted-foreground">{provider.avg_response_time}s avg</div>
                                )}
                              </div>
                            )}
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleTestProvider(provider.id)}
                              disabled={testingProvider === provider.id}
                              title="Test/Sanity Check Provider"
                            >
                              {testingProvider === provider.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <PlayCircle className="h-4 w-4" />
                              )}
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleEditProvider(provider)}
                              title="Edit Provider"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleDeleteProvider(provider.id)}
                              className="text-red-500 hover:text-red-700"
                              title="Delete Provider"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        <div className="mt-3 pt-3 border-t border-border space-y-2">
                          <div className="flex items-center space-x-2">
                            <Key className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">
                              API Key: {provider.api_key_masked || 'Not configured'}
                            </span>
                          </div>
                          {testResult && testResult.provider_id === provider.id && (
                            <div className={`mt-2 p-2 rounded-md text-sm ${
                              testResult.success 
                                ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' 
                                : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                            }`}>
                              <div className="flex items-center space-x-2">
                                {testResult.success ? (
                                  <>
                                    <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                                    <span className="text-green-800 dark:text-green-200 font-medium">Test Passed</span>
                                  </>
                                ) : (
                                  <>
                                    <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
                                    <span className="text-red-800 dark:text-red-200 font-medium">Test Failed</span>
                                  </>
                                )}
                              </div>
                              {testResult.success ? (
                                <div className="mt-1 text-green-700 dark:text-green-300">
                                  <div>Response: {testResult.response || 'No response'}</div>
                                  <div className="text-xs mt-1">
                                    Response time: {testResult.response_time_seconds}s • Tokens: {testResult.tokens_used || 0}
                                  </div>
                                </div>
                              ) : (
                                <div className="mt-1 text-red-700 dark:text-red-300">
                                  <div>{testResult.error || 'Unknown error'}</div>
                                  {testResult.error_code && (
                                    <div className="text-xs mt-1">Error code: {testResult.error_code}</div>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Add/Edit Provider Dialog */}
          <Dialog open={showProviderDialog} onOpenChange={setShowProviderDialog}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>
                  {editingProvider ? 'Edit LLM Provider' : 'Add LLM Provider'}
                </DialogTitle>
                <DialogDescription>
                  Configure an LLM provider for artifact evaluation
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      placeholder="e.g., GPT-4 Primary"
                      value={providerForm.name}
                      onChange={(e) => setProviderForm({ ...providerForm, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="provider">Provider</Label>
                    <Select
                      value={providerForm.provider}
                      onValueChange={(value) => {
                        setProviderForm({ ...providerForm, provider: value, model: '' })
                        setAvailableModels([]) // Clear models when provider changes
                        setModelDetectionError(null)
                      }}
                    >
                      <SelectTrigger id="provider">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openai">OpenAI</SelectItem>
                        <SelectItem value="anthropic">Anthropic</SelectItem>
                        <SelectItem value="azure">Azure OpenAI</SelectItem>
                        <SelectItem value="local">Local Model</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="model">Model</Label>
                    <div className="flex space-x-2 items-start">
                      <div className="flex-1 min-w-0">
                        <Select
                          value={providerForm.model}
                          onValueChange={(value) => setProviderForm({ ...providerForm, model: value })}
                          disabled={availableModels.length === 0}
                        >
                          <SelectTrigger id="model" className="w-full">
                            <SelectValue placeholder={availableModels.length > 0 ? "Select a model" : "Enter API key and click Detect"} />
                          </SelectTrigger>
                          <SelectContent>
                            {availableModels.map((model) => (
                              <SelectItem key={model.id} value={model.id}>
                                {model.name || model.id}
                                {model.description && ` - ${model.description}`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={detectModels}
                        disabled={detectingModels || !providerForm.api_key || !providerForm.provider}
                        title="Detect available models from provider"
                        className="shrink-0 flex-shrink-0"
                      >
                        {detectingModels ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Zap className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    {modelDetectionError && (
                      <p className="text-sm text-red-500">{modelDetectionError}</p>
                    )}
                    {availableModels.length > 0 && (
                      <p className="text-xs text-muted-foreground">
                        Found {availableModels.length} model(s). Select one above or enter manually.
                      </p>
                    )}
                    {availableModels.length === 0 && providerForm.api_key && (
                      <p className="text-xs text-muted-foreground">
                        Click the lightning icon to detect available models, or enter model name manually.
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="status">Status</Label>
                    <Select
                      value={providerForm.status}
                      onValueChange={(value) => setProviderForm({ ...providerForm, status: value })}
                    >
                      <SelectTrigger id="status" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="backup">Backup</SelectItem>
                        <SelectItem value="inactive">Inactive</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="api_key">API Key</Label>
                  <Input
                    id="api_key"
                    type="password"
                    placeholder={editingProvider ? "Leave blank to keep existing" : "Enter API key"}
                    value={providerForm.api_key}
                    onChange={(e) => {
                      setProviderForm({ ...providerForm, api_key: e.target.value })
                      // Clear models when API key changes (user might be entering different key)
                      if (availableModels.length > 0) {
                        setAvailableModels([])
                        setModelDetectionError(null)
                      }
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    Enter your API key and click the lightning icon next to Model to auto-detect available models.
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="base_url">Base URL (Optional)</Label>
                  <Input
                    id="base_url"
                    placeholder="https://api.openai.com/v1 (leave blank for default)"
                    value={providerForm.base_url}
                    onChange={(e) => setProviderForm({ ...providerForm, base_url: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Input
                    id="description"
                    placeholder="Usage notes or description"
                    value={providerForm.description}
                    onChange={(e) => setProviderForm({ ...providerForm, description: e.target.value })}
                  />
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={providerForm.is_default}
                      onCheckedChange={(checked) => setProviderForm({ ...providerForm, is_default: checked })}
                    />
                    <Label>Set as default provider</Label>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowProviderDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveProvider}>
                  <Save className="h-4 w-4 mr-2" />
                  {editingProvider ? 'Update' : 'Create'} Provider
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        <TabsContent value="prompts" className="space-y-6">
          <PromptTemplates />
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="h-5 w-5" />
                <span>Notification Preferences</span>
              </CardTitle>
              <CardDescription>Configure alerts and notification settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Email Alerts</div>
                    <div className="text-xs text-muted-foreground">
                      Receive email notifications for important events
                    </div>
                  </div>
                  <Switch
                    checked={notifications.emailAlerts}
                    onCheckedChange={(checked) => 
                      setNotifications(prev => ({ ...prev, emailAlerts: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">System Health Alerts</div>
                    <div className="text-xs text-muted-foreground">
                      Notifications when system performance degrades
                    </div>
                  </div>
                  <Switch
                    checked={notifications.systemHealth}
                    onCheckedChange={(checked) => 
                      setNotifications(prev => ({ ...prev, systemHealth: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Job Failure Alerts</div>
                    <div className="text-xs text-muted-foreground">
                      Immediate notifications when jobs fail
                    </div>
                  </div>
                  <Switch
                    checked={notifications.jobFailures}
                    onCheckedChange={(checked) => 
                      setNotifications(prev => ({ ...prev, jobFailures: checked }))
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Weekly Reports</div>
                    <div className="text-xs text-muted-foreground">
                      Weekly summary reports via email
                    </div>
                  </div>
                  <Switch
                    checked={notifications.weeklyReports}
                    onCheckedChange={(checked) => 
                      setNotifications(prev => ({ ...prev, weeklyReports: checked }))
                    }
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <label className="text-sm font-medium">Notification Email</label>
                <Input type="email" defaultValue="admin@aulendur.com" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-6">
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5" />
                <span>User Management</span>
              </CardTitle>
              <CardDescription>Manage user accounts and permissions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {users.map((user) => (
                  <Card key={user.id} className="aulendur-hover-transform">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                            <span className="text-sm font-bold">{user.name.split(' ').map(n => n[0]).join('')}</span>
                          </div>
                          <div>
                            <div className="font-medium flex items-center space-x-2">
                              <span>{user.name}</span>
                              <Badge variant={user.status === 'active' ? 'default' : 'secondary'}>
                                {user.status}
                              </Badge>
                            </div>
                            <div className="text-sm text-muted-foreground">{user.email}</div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right text-sm">
                            <div>{user.role}</div>
                            <div className="text-muted-foreground">Last login: {user.lastLogin}</div>
                          </div>
                          <Button variant="outline" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card className="aulendur-gradient-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Security Settings</span>
              </CardTitle>
              <CardDescription>Configure security and access controls</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Session Timeout (minutes)</label>
                  <Input type="number" defaultValue="60" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Login Attempts</label>
                  <Input type="number" defaultValue="5" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Password Min Length</label>
                  <Input type="number" defaultValue="8" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">API Rate Limit (req/min)</label>
                  <Input type="number" defaultValue="100" />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Two-Factor Authentication</div>
                    <div className="text-xs text-muted-foreground">
                      Require 2FA for all user accounts
                    </div>
                  </div>
                  <Switch defaultChecked={true} />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">Audit Logging</div>
                    <div className="text-xs text-muted-foreground">
                      Log all user actions and system events
                    </div>
                  </div>
                  <Switch defaultChecked={true} />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="text-sm font-medium">IP Whitelisting</div>
                    <div className="text-xs text-muted-foreground">
                      Restrict access to specific IP addresses
                    </div>
                  </div>
                  <Switch defaultChecked={false} />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Settings

