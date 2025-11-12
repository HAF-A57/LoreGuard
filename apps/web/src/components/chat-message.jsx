import { Badge } from '@/components/ui/badge.jsx'
import { MarkdownMessage } from '@/components/ui/markdown-message.jsx'
import { Bot, User, Sparkles } from 'lucide-react'

/**
 * Reusable component for rendering individual chat messages
 * Handles both user and assistant message display with proper styling
 */
export function ChatMessage({ message }) {
  return (
    <div className="space-y-2">
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
          {/* Show tool usage prominently - without message bubble background */}
          {message.tool_calls && message.tool_calls.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {message.tool_calls.map((tc, idx) => {
                const toolName = tc.function.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                return (
                  <div 
                    key={idx} 
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#213C4E]/30 via-[#5C798B]/30 to-[#7B949C]/30 border border-[#5C798B]/50 shadow-sm backdrop-blur-sm"
                  >
                    <div className="relative tool-icon-glow">
                      <Sparkles 
                        className="h-4 w-4" 
                        style={{ 
                          background: 'linear-gradient(135deg, #D4AF37 0%, #FFD700 25%, #FFFFFF 50%, #FFD700 75%, #D4AF37 100%)',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                          backgroundClip: 'text',
                          filter: 'drop-shadow(0 0 3px rgba(212, 175, 55, 0.6)) drop-shadow(0 1px 2px rgba(255, 255, 255, 0.8))'
                        }} 
                      />
                    </div>
                    <span className="text-xs font-medium text-sidebar-foreground">
                      Using my <span className="font-semibold" style={{ color: '#FFD700' }}>{toolName}</span> tool...
                    </span>
                  </div>
                )
              })}
            </div>
          )}

          {/* Message content - only show bubble if there's actual content or no tool calls */}
          {(!message.tool_calls || message.tool_calls.length === 0 || message.content) && (
            <div className={`inline-block p-3 rounded-lg max-w-full break-words overflow-hidden ${
              message.type === 'user'
                ? 'bg-primary text-white'
                : 'bg-muted'
            }`}>
              {message.type === 'assistant' ? (
                <div className="text-sm max-w-full break-words" style={{ overflowWrap: 'anywhere', wordBreak: 'break-word' }}>
                  <MarkdownMessage 
                    content={message.content} 
                    isUserMessage={false}
                  />
                </div>
              ) : (
                <p className="text-sm whitespace-pre-wrap break-words" style={{ overflowWrap: 'anywhere' }}>{message.content}</p>
              )}
            </div>
          )}
          <div className="flex items-center space-x-2 mt-1">
            <p className="text-xs text-sidebar-foreground/60">
              {new Date(message.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

