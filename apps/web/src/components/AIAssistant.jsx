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
  ThumbsDown
} from 'lucide-react'

const AIAssistant = ({ isCollapsed, onToggleCollapse, onClose }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: "Hello! I'm your LoreGuard AI Assistant. I can help you analyze artifacts, understand evaluation criteria, navigate the system, and answer questions about your data. How can I assist you today?",
      timestamp: new Date().toISOString(),
      suggestions: [
        "Explain this artifact's significance",
        "What are the current evaluation criteria?",
        "Show me recent Signal artifacts",
        "How do I configure sources?"
      ]
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: generateAIResponse(inputValue),
        timestamp: new Date().toISOString(),
        suggestions: generateSuggestions(inputValue)
      }
      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)
    }, 1500)
  }

  const generateAIResponse = (input) => {
    const responses = {
      'artifact': "I can help you analyze artifacts in your LoreGuard system. Artifacts are evaluated using our Military Wargaming Relevance Rubric, which considers Strategic Relevance (30%), Source Credibility (25%), Temporal Relevance (20%), Geographic Scope (15%), and Actionable Intelligence (10%). Would you like me to explain any specific artifact or evaluation criteria?",
      'source': "LoreGuard currently monitors 47 active sources including NATO Strategic Communications, International Economic Forum, and Cybersecurity Research Institute. Sources are automatically crawled based on their configured schedules. You can manage sources in the Sources page. Would you like help configuring a new source?",
      'evaluation': "The evaluation system uses AI models to assess artifact relevance for military wargaming scenarios. The current active rubric (v2.1) has a 94.2% accuracy rate. Artifacts are classified as Signal (high-value), Review (moderate value), or Noise (low value). What specific aspect of evaluation would you like to understand better?",
      'signal': "Signal artifacts are high-value artifacts that meet our relevance criteria with high confidence scores. Currently, you have 892 Signal artifacts in your library. These are curated for distribution to the wargaming community. Would you like me to show you the latest Signal artifacts or help you understand the classification criteria?"
    }

    const lowerInput = input.toLowerCase()
    for (const [key, response] of Object.entries(responses)) {
      if (lowerInput.includes(key)) {
        return response
      }
    }

    return "I understand you're asking about LoreGuard functionality. I can help with artifact analysis, source management, evaluation criteria, system navigation, and data insights. Could you be more specific about what you'd like to know?"
  }

  const generateSuggestions = (input) => {
    const suggestionSets = {
      'artifact': [
        "Show artifact confidence scores",
        "Explain evaluation criteria",
        "Find similar artifacts",
        "Export artifact analysis"
      ],
      'source': [
        "Add new source",
        "Check source health",
        "Configure crawl schedule",
        "View source analytics"
      ],
      'evaluation': [
        "View rubric details",
        "Check evaluation history",
        "Adjust confidence thresholds",
        "Compare model performance"
      ],
      'default': [
        "Show system overview",
        "Recent activity summary",
        "Help with navigation",
        "System configuration"
      ]
    }

    const lowerInput = input.toLowerCase()
    for (const [key, suggestions] of Object.entries(suggestionSets)) {
      if (lowerInput.includes(key)) {
        return suggestions
      }
    }
    return suggestionSets.default
  }

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion)
    inputRef.current?.focus()
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  if (isCollapsed) {
    return (
      <div className="w-12 bg-sidebar border-l border-sidebar-border flex flex-col items-center py-4">
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

  return (
    <div className="w-80 bg-sidebar border-l border-sidebar-border flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border ai-assistant-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-sidebar-foreground">AI Assistant</h3>
              <p className="text-xs text-sidebar-foreground/70">LoreGuard Helper</p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="sm" onClick={onToggleCollapse} className="text-sidebar-foreground hover:text-sidebar-accent-foreground">
              <Minimize2 className="h-4 w-4" />
            </Button>
            {onClose && (
              <Button variant="ghost" size="sm" onClick={onClose} className="text-sidebar-foreground hover:text-sidebar-accent-foreground">
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className="space-y-2">
              <div className={`flex items-start space-x-3 ${
                message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
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
                <div className={`flex-1 ${
                  message.type === 'user' ? 'text-right' : ''
                }`}>
                  <div className={`inline-block p-3 rounded-lg max-w-full ${
                    message.type === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-muted'
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>

              {/* Suggestions */}
              {message.suggestions && message.type === 'assistant' && (
                <div className="ml-11 space-y-2">
                  <p className="text-xs text-muted-foreground">Suggested actions:</p>
                  <div className="flex flex-wrap gap-2">
                    {message.suggestions.map((suggestion, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        className="text-xs h-7"
                        onClick={() => handleSuggestionClick(suggestion)}
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
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
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t border-sidebar-border">
        <div className="flex space-x-2">
          <Input
            ref={inputRef}
            placeholder="Ask me anything about LoreGuard..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1"
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className="aulendur-hover-transform"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Quick Actions */}
        <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
          <div className="flex items-center space-x-3">
            <Button variant="ghost" size="sm" className="h-6 text-xs">
              <Lightbulb className="h-3 w-3 mr-1" />
              Tips
            </Button>
            <Button variant="ghost" size="sm" className="h-6 text-xs">
              <Brain className="h-3 w-3 mr-1" />
              Examples
            </Button>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Online</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIAssistant

