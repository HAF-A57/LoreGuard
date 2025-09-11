import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Switch } from '@/components/ui/switch.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
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
  Edit,
  Trash2
} from 'lucide-react'

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

  // Mock data for LLM models
  const llmModels = [
    {
      id: 1,
      name: "GPT-4",
      provider: "OpenAI",
      status: "active",
      usage: "Primary evaluation model",
      apiKey: "sk-...abc123",
      costPerToken: 0.03,
      avgResponseTime: 1.2
    },
    {
      id: 2,
      name: "Claude-3",
      provider: "Anthropic",
      status: "backup",
      usage: "Secondary evaluation model",
      apiKey: "sk-...def456",
      costPerToken: 0.025,
      avgResponseTime: 1.8
    },
    {
      id: 3,
      name: "Llama-2",
      provider: "Meta",
      status: "inactive",
      usage: "Experimental model",
      apiKey: "Not configured",
      costPerToken: 0.01,
      avgResponseTime: 2.1
    }
  ]

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
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="models">AI Models</TabsTrigger>
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
              <CardTitle className="flex items-center space-x-2">
                <Brain className="h-5 w-5" />
                <span>AI Model Configuration</span>
              </CardTitle>
              <CardDescription>Manage LLM models for artifact evaluation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {llmModels.map((model) => (
                  <Card key={model.id} className="aulendur-hover-transform">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div>
                            <div className="font-medium flex items-center space-x-2">
                              <span>{model.name}</span>
                              <Badge variant={
                                model.status === 'active' ? 'default' : 
                                model.status === 'backup' ? 'secondary' : 'outline'
                              }>
                                {model.status}
                              </Badge>
                            </div>
                            <div className="text-sm text-muted-foreground">{model.provider} • {model.usage}</div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right text-sm">
                            <div>${model.costPerToken}/token</div>
                            <div className="text-muted-foreground">{model.avgResponseTime}s avg</div>
                          </div>
                          <Button variant="outline" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="mt-3 pt-3 border-t border-border">
                        <div className="flex items-center space-x-2">
                          <Key className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">API Key: {model.apiKey}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
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

