import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  FileText, 
  Search,
  Brain,
  Lightbulb,
  MessageSquare,
  Minimize2,
  Maximize2,
  X,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  History,
  Plus,
  MoreVertical,
  Trash2,
  Archive
} from 'lucide-react'
import { ASSISTANT_API_URL } from '@/config.js'
import { toast } from 'sonner'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu.jsx'

const AIAssistant = ({ isCollapsed, onToggleCollapse, onClose }) => {
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showSessionList, setShowSessionList] = useState(false)
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
  }

  if (isCollapsed) {
    return (
      <div className="w-12 bg-sidebar border-l border-sidebar-border flex flex-col items-center py-4 flex-shrink-0 h-full">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="aulendur-hover-transform text-sidebar-foreground hover:text-sidebar-accent-foreground"
        >
          <MessageSquare className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  // Get current session info
  const currentSession = sessions.find(s => s.id === currentSessionId)

  return (
    <div className="w-80 bg-sidebar border-l border-sidebar-border flex flex-col flex-shrink-0 h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border ai-assistant-header">
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
          <div className="text-xs text-sidebar-foreground/70">
            {currentSession.title}
          </div>
        )}
      </div>

      {/* Session List Overlay */}
      {showSessionList && (
        <div className="absolute top-16 left-0 right-0 bottom-0 bg-sidebar z-10 flex flex-col">
          <div className="p-4 border-b border-sidebar-border">
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
          <ScrollArea className="flex-1">
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
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                              <MoreVertical className="h-3 w-3" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem onClick={(e) => handleDeleteSession(session.id, e)}>
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
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
      <ScrollArea className="flex-1 p-4 min-h-0">
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
              <div key={message.id} className="space-y-2">
                <div className={`flex items-start space-x-3 ${
                  message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}>
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    message.type === 'user' 
                      ? 'bg-primary' 
                      : 'bg-muted'
                  }`}>
                    {message.type === 'user' ? (
                      <User className="h-4 w-4 text-white" />
                    ) : (
                      <Bot className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <div className={`flex-1 min-w-0 ${
                    message.type === 'user' ? 'text-right' : ''
                  }`}>
                    <div className={`inline-block p-3 rounded-lg max-w-full break-words ${
                      message.type === 'user'
                        ? 'bg-primary text-white'
                        : 'bg-muted'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      
                      {/* Show tool usage badge */}
                      {message.tool_calls && message.tool_calls.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {message.tool_calls.map((tc, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              <Sparkles className="h-3 w-3 mr-1" />
                              {tc.function.name}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 mt-1">
                      <p className="text-xs text-muted-foreground">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </p>
                      {message.model_used && message.type === 'assistant' && (
                        <Badge variant="outline" className="text-xs">
                          {message.model_used}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
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
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t border-sidebar-border flex-shrink-0">
        <div className="flex space-x-2">
          <Input
            ref={inputRef}
            placeholder="Ask me anything about LoreGuard..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1 bg-sidebar-accent/20 text-sidebar-foreground placeholder:text-sidebar-foreground/60 border-sidebar-border focus-visible:ring-sidebar-ring"
            disabled={isTyping}
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className="aulendur-hover-transform"
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
  )
}

export default AIAssistant
