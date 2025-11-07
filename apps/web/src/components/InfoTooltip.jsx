import { Info } from 'lucide-react'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip.jsx'
import { cn } from '@/lib/utils.js'

const InfoTooltip = ({ content, llmBound = false, className }) => {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className={cn(
            "inline-flex items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            className
          )}
          aria-label="More information"
        >
          <Info className={cn(
            "h-4 w-4",
            llmBound ? "text-blue-500" : "text-muted-foreground"
          )} />
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-sm" side="right">
        <div className="space-y-2">
          {llmBound && (
            <div className="flex items-center space-x-1 text-blue-300 text-xs font-semibold">
              <span>🤖 LLM-Bound</span>
            </div>
          )}
          <div className="text-sm">{content}</div>
        </div>
      </TooltipContent>
    </Tooltip>
  )
}

export default InfoTooltip

