import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import { Code2, ExternalLink } from 'lucide-react'

/**
 * Reusable component for rendering markdown content in chat messages
 * Supports GitHub Flavored Markdown (GFM) including tables, code blocks, etc.
 * Styled to work with LoreGuard's theme system (light/dark mode)
 */
export function MarkdownMessage({ 
  content, 
  className,
  isUserMessage = false 
}) {
  return (
    <div className={cn("markdown-content text-sidebar-foreground max-w-full break-words", className)} style={{ overflowWrap: 'anywhere', wordBreak: 'break-word' }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ node, ...props }) => (
            <h1 className="text-xl font-bold mt-4 mb-2 first:mt-0 text-sidebar-foreground" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-lg font-semibold mt-3 mb-2 first:mt-0 text-sidebar-foreground" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-base font-semibold mt-3 mb-1 first:mt-0 text-sidebar-foreground" {...props} />
          ),
          // Paragraphs
          p: ({ node, ...props }) => (
            <p className="mb-2 last:mb-0 leading-relaxed text-sidebar-foreground break-words" style={{ overflowWrap: 'anywhere' }} {...props} />
          ),
          // Lists
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside mb-2 space-y-1 ml-4" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside mb-2 space-y-1 ml-4" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="leading-relaxed" {...props} />
          ),
          // Links - enhanced visibility for dark mode
          a: ({ node, ...props }) => (
            <a
              className="markdown-link underline inline-flex items-center gap-1 transition-colors font-medium"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            >
              {props.children}
              <ExternalLink className="h-3 w-3 opacity-90" />
            </a>
          ),
          // Code blocks
          code: ({ node, inline, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '')
            return !inline ? (
              <div className="relative my-2">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 border-b border-border rounded-t-md">
                  <Code2 className="h-3 w-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground font-mono">
                    {match ? match[1] : 'code'}
                  </span>
                </div>
                <pre
                  className={cn(
                    "overflow-x-auto p-3 rounded-b-md bg-muted/30 border border-t-0 border-border",
                    "font-mono text-sm leading-relaxed"
                  )}
                  {...props}
                >
                  <code className={className} {...props}>
                    {children}
                  </code>
                </pre>
              </div>
            ) : (
              <code
                className="px-1.5 py-0.5 rounded bg-muted/50 font-mono text-sm border border-border"
                {...props}
              >
                {children}
              </code>
            )
          },
          // Blockquotes
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-primary/30 pl-4 py-1 my-2 italic bg-muted/30 rounded-r text-sidebar-foreground/90"
              {...props}
            />
          ),
          // Tables
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-2 max-w-full">
              <table className="min-w-full border-collapse border border-border rounded-md max-w-full" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-muted/50" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="border border-border px-3 py-2 text-left font-semibold text-sm" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border border-border px-3 py-2 text-sm" {...props} />
          ),
          // Horizontal rule
          hr: ({ node, ...props }) => (
            <hr className="my-4 border-border" {...props} />
          ),
          // Strong/Bold
          strong: ({ node, ...props }) => (
            <strong className="font-semibold" {...props} />
          ),
          // Emphasis/Italic
          em: ({ node, ...props }) => (
            <em className="italic" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

