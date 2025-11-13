import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { ChatMessage } from '@/components/chat-message.jsx'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible.jsx'
import { 
  Send, 
  Bot, 
  MessageSquare,
  Minimize2,
  X,
  Loader2,
  History,
  Plus,
  MoreVertical,
  Trash2,
  ChevronsLeft,
  ChevronsRight,
  ChevronDown,
  ChevronUp,
  Sparkles
} from 'lucide-react'
import { ASSISTANT_API_URL } from '@/config.js'
import { toast } from 'sonner'

// Assistant tools data
const ASSISTANT_TOOLS = [
  {
    name: "get_rubric_details",
    title: "Get Rubric Details",
    description: "Get detailed information about a specific rubric version or the active rubric",
    example: "What rubrics do I have configured? Show me the active rubric details."
  },
  {
    name: "search_artifacts",
    title: "Search Artifacts",
    description: "Search for artifacts by title, organization, or topic",
    example: "Show me my recent Signal artifacts about China"
  },
  {
    name: "get_artifact_details",
    title: "Get Artifact Details",
    description: "Get detailed information about a specific artifact including metadata and evaluation",
    example: "Tell me more about artifact [artifact-id]"
  },
  {
    name: "list_sources",
    title: "List Sources",
    description: "List all configured data sources with their status",
    example: "What sources am I monitoring? Show me all active sources."
  },
  {
    name: "trigger_source_crawl",
    title: "Trigger Source Crawl",
    description: "Trigger a manual crawl for a specific source",
    example: "Start a crawl for the Brookings Institution source"
  },
  {
    name: "get_job_status",
    title: "Get Job Status",
    description: "Get status and details of a specific job",
    example: "What's the status of job [job-id]?"
  },
  {
    name: "list_active_jobs",
    title: "List Active Jobs",
    description: "List all currently active (running or pending) jobs",
    example: "Show me all currently running jobs"
  },
  {
    name: "evaluate_artifact",
    title: "Evaluate Artifact",
    description: "Trigger evaluation for a specific artifact using the active rubric",
    example: "Evaluate artifact [artifact-id] using the active rubric"
  },
  {
    name: "get_system_health",
    title: "Get System Health",
    description: "Get overall system health status including all services",
    example: "What's the system health status? Are all services running?"
  }
]

const AIAssistant = ({ isCollapsed, onToggleCollapse, onClose }) => {
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showSessionList, setShowSessionList] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [showToolsExplorer, setShowToolsExplorer] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load chat sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  // Load current session messages
  useEffect(() => {
    if (currentSessionId) {
      loadSessionMessages(currentSessionId)
    }
  }, [currentSessionId])

  const loadSessions = async () => {
    try {
      const response = await fetch(`${ASSISTANT_API_URL}/api/v1/chat/sessions?limit=50`)
      if (response.ok) {
        const data = await response.json()
        setSessions(data.items || [])
        
        // Auto-select most recent session if none selected
        if (!currentSessionId && data.items && data.items.length > 0) {
          setCurrentSessionId(data.items[0].id)
        }
      }
    } catch (error) {
      console.error('Error loading sessions:', error)
    }
  }

  const loadSessionMessages = async (sessionId) => {
    try {
      setIsLoading(true)
      const response = await fetch(`${ASSISTANT_API_URL}/api/v1/chat/sessions/${sessionId}`)
      if (response.ok) {
        const session = await response.json()
        
        // Convert messages to display format
        const displayMessages = session.messages.map(msg => ({
          id: msg.id,
          type: msg.role === 'user' ? 'user' : 'assistant',
          role: msg.role,
          content: msg.content,
          timestamp: msg.created_at,
          tool_calls: msg.tool_calls,
          model_used: msg.model_used
        }))
        
        setMessages(displayMessages)
      }
    } catch (error) {
      console.error('Error loading session messages:', error)
      toast.error('Failed to load conversation')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isTyping) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setIsTyping(true)

    // Optimistically add user message to UI
    const tempUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      const response = await fetch(`${ASSISTANT_API_URL}/api/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: currentSessionId,
          use_tools: true,
          include_context: true
        })
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(error.detail || 'Request failed')
      }

      const data = await response.json()
      
      // Update current session ID if new session was created
      if (!currentSessionId && data.session_id) {
        setCurrentSessionId(data.session_id)
        loadSessions() // Refresh session list
      }

      // Add assistant response
      const assistantMessage = {
        id: data.assistant_message.id,
        type: 'assistant',
        role: data.assistant_message.role,
        content: data.assistant_message.content,
        timestamp: data.assistant_message.created_at,
        tool_calls: data.assistant_message.tool_calls,
        model_used: data.assistant_message.model_used,
        tokensUsed: data.tokens_used,
        toolsUsed: data.tools_used
      }

      setMessages(prev => [...prev, assistantMessage])

      // Show toast if tools were used
      if (data.tools_used && data.tools_used.length > 0) {
        toast.success(`Used tools: ${data.tools_used.join(', ')}`)
      }

    } catch (error) {
      console.error('Error sending message:', error)
      toast.error(`Failed to send message: ${error.message}`)
      
      // Add error message
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        type: 'assistant',
        content: `I apologize, but I encountered an error: ${error.message}. Please try again.`,
        timestamp: new Date().toISOString()
      }])
    } finally {
      setIsTyping(false)
    }
  }

  const handleNewChat = () => {
    setCurrentSessionId(null)
    setMessages([])
    setShowSessionList(false)
  }

  const handleSelectSession = (sessionId) => {
    setCurrentSessionId(sessionId)
    setShowSessionList(false)
  }

  const handleDeleteSession = async (sessionId, event) => {
    event.stopPropagation()
    
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return
    }

    try {
      const response = await fetch(`${ASSISTANT_API_URL}/api/v1/chat/sessions/${sessionId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        toast.success('Conversation deleted')
        loadSessions()
        
        if (sessionId === currentSessionId) {
          handleNewChat()
        }
      }
    } catch (error) {
      console.error('Error deleting session:', error)
      toast.error('Failed to delete conversation')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
    // Shift+Enter allows new line, handled by textarea default behavior
  }

  // Auto-resize textarea based on content
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`
    }
  }, [inputValue])

  // Get current session info
  const currentSession = sessions.find(s => s.id === currentSessionId)

  return (
    <div className={`bg-sidebar border-l border-sidebar-border flex flex-col flex-shrink-0 h-full max-h-full overflow-hidden transition-all duration-300 ease-in-out relative ai-assistant-container ${
      isCollapsed ? 'w-12' : isExpanded ? 'w-[640px]' : 'w-80'
    }`}>
      {/* Collapsed state - icon button */}
      <div className={`flex flex-col items-center py-4 h-full transition-opacity duration-300 ease-in-out ${
        isCollapsed ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none absolute inset-0'
      }`}>
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="lgcustom-hover-transform text-sidebar-foreground hover:text-sidebar-accent-foreground"
        >
          <MessageSquare className="h-4 w-4" />
        </Button>
      </div>

      {/* Expand/Collapse Width Button */}
      {!isCollapsed && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 z-20 h-8 w-8 p-0 bg-sidebar border border-sidebar-border rounded-full shadow-lg hover:bg-sidebar-accent transition-all duration-300 ease-in-out"
          title={isExpanded ? "Collapse width" : "Expand width"}
        >
          {isExpanded ? (
            <ChevronsRight className="h-4 w-4 text-sidebar-foreground" />
          ) : (
            <ChevronsLeft className="h-4 w-4 text-sidebar-foreground" />
          )}
        </Button>
      )}

      {/* Expanded state - full assistant */}
      {!isCollapsed && (
      <div className="flex flex-col h-full max-h-full w-full transition-opacity duration-300 ease-in-out overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border ai-assistant-header flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-sidebar-foreground">AI Assistant</h3>
              <p className="text-xs text-sidebar-foreground/70">Context-Aware</p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setShowSessionList(!showSessionList)}
              className="text-sidebar-foreground hover:text-sidebar-accent-foreground"
              title="Chat History"
            >
              <History className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleNewChat}
              className="text-sidebar-foreground hover:text-sidebar-accent-foreground"
              title="New Chat"
            >
              <Plus className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onToggleCollapse} 
              className="text-sidebar-foreground hover:text-sidebar-accent-foreground"
            >
              <Minimize2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Current Session Info */}
        {currentSession && (
          <div className="text-xs text-sidebar-foreground/70 mb-2">
            {currentSession.title}
          </div>
        )}

        {/* Explore Assistant Tools - Always visible in header */}
        <Collapsible open={showToolsExplorer} onOpenChange={setShowToolsExplorer} className="w-full">
          <CollapsibleTrigger asChild>
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full text-xs h-7 bg-sidebar-accent/20 border-sidebar-border text-sidebar-foreground hover:bg-sidebar-accent/30 hover:text-sidebar-foreground"
            >
              <Sparkles className="h-3 w-3 mr-1.5" />
              Explore Assistant Tools
              {showToolsExplorer ? (
                <ChevronUp className="h-3 w-3 ml-auto" />
              ) : (
                <ChevronDown className="h-3 w-3 ml-auto" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="w-full mt-2">
            <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
              {ASSISTANT_TOOLS.map((tool) => (
                <Card key={tool.name} className="bg-sidebar-accent/20 border-sidebar-border py-1.5">
                  <CardHeader className="pb-1 px-3 pt-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 mb-0.5">
                          <CardTitle className="text-xs font-semibold text-sidebar-foreground leading-tight">
                            {tool.title}
                          </CardTitle>
                          <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 shrink-0 bg-sidebar-accent/30 border-sidebar-border text-sidebar-foreground">
                            <Sparkles className="h-2 w-2 mr-0.5" />
                            Tool
                          </Badge>
                        </div>
                        <CardDescription className="text-[10px] text-sidebar-foreground/70 leading-tight line-clamp-1">
                          {tool.description}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0 px-3 pb-1.5">
                    <div className="text-[10px]">
                      <span className="text-sidebar-foreground/60 font-medium">Example: </span>
                      <button
                        onClick={() => {
                          setInputValue(tool.example)
                          setShowToolsExplorer(false)
                          inputRef.current?.focus()
                        }}
                        className="text-sidebar-foreground hover:text-sidebar-accent-foreground underline text-left break-words"
                      >
                        {tool.example}
                      </button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>

      {/* Session List Overlay */}
      {showSessionList && (
        <div className="absolute inset-0 bg-sidebar z-10 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-sidebar-border flex-shrink-0">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-sidebar-foreground">Chat History</h3>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowSessionList(false)}
                className="text-sidebar-foreground"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <ScrollArea className="flex-1 min-h-0 overflow-hidden">
            <div className="p-4 space-y-2">
              {sessions.length === 0 ? (
                <div className="text-center py-8 text-sidebar-foreground/70">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No conversations yet</p>
                </div>
              ) : (
                sessions.map(session => (
                  <Card 
                    key={session.id}
                    className={`cursor-pointer hover:bg-accent transition-colors ${
                      session.id === currentSessionId ? 'ring-2 ring-primary' : ''
                    }`}
                    onClick={() => handleSelectSession(session.id)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between mb-1">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm line-clamp-1">
                            {session.title || 'Untitled'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {session.message_count} messages
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 hover:text-destructive"
                          onClick={(e) => handleDeleteSession(session.id, e)}
                          title="Delete conversation"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                      {session.last_message_preview && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {session.last_message_preview}
                        </p>
                      )}
                      <div className="text-xs text-muted-foreground mt-1">
                        {new Date(session.updated_at).toLocaleDateString()}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 min-h-0 overflow-hidden w-full">
        <div className="p-4 w-full max-w-full overflow-x-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Bot className="h-12 w-12 text-muted-foreground mb-4" />
            <h4 className="font-semibold text-sidebar-foreground mb-2">
              Welcome to LoreGuard AI Assistant
            </h4>
            <p className="text-sm text-sidebar-foreground/70 mb-4">
              I can help you analyze artifacts, manage rubrics, trigger crawls, and navigate your LoreGuard environment.
            </p>

            <div className="space-y-2 w-full">
              <p className="text-xs text-sidebar-foreground/70">Try asking:</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full text-xs"
                onClick={() => setInputValue("What rubrics do I have configured?")}
              >
                What rubrics do I have configured?
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full text-xs"
                onClick={() => setInputValue("Show me my recent Signal artifacts")}
              >
                Show me my recent Signal artifacts
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full text-xs"
                onClick={() => setInputValue("What sources am I monitoring?")}
              >
                What sources am I monitoring?
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-muted rounded-lg flex items-center justify-center">
                  <Bot className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t border-sidebar-border flex-shrink-0">
        <div className="flex space-x-2 items-end">
          <div className="flex-1 relative">
            <Textarea
              ref={inputRef}
              placeholder="Ask me anything about LoreGuard... (Shift+Enter for new line)"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              className="min-h-[44px] max-h-[200px] resize-none bg-sidebar-accent/20 text-sidebar-foreground placeholder:text-sidebar-foreground/60 border-sidebar-border focus-visible:ring-sidebar-ring pr-12"
              disabled={isTyping}
              rows={1}
            />
            <div className="absolute bottom-2 right-2 text-xs text-sidebar-foreground/60 pointer-events-none">
              {inputValue.length > 0 && `${inputValue.length} chars`}
            </div>
          </div>
          <Button 
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className="lgcustom-hover-transform h-[44px] flex-shrink-0"
            size="default"
          >
            {isTyping ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        
        {/* Info Text */}
        <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Connected</span>
          </div>
          {currentSession && (
            <span>{currentSession.total_tokens || 0} tokens</span>
          )}
        </div>
      </div>
      </div>
      )}
    </div>
  )
}

export default AIAssistant
