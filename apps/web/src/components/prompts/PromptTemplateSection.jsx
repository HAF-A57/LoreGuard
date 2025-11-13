/**
 * PromptTemplateSection Component
 * Reusable section component for displaying templates of a specific type
 * Each section is independently scrollable
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import PromptTemplateCard from './PromptTemplateCard.jsx'
import { 
  FileCode, 
  MessageSquare, 
  CheckSquare,
  Loader2
} from 'lucide-react'

const PROMPT_TYPE_CONFIG = {
  metadata: {
    label: 'Extraction',
    description: 'Metadata extraction templates',
    explanation: 'Extracts structured metadata (topics, organizations, authors, dates) from raw documents to enable filtering and categorization.',
    icon: FileCode,
    color: 'bg-blue-500',
    iconBgColor: 'bg-blue-500/10 dark:bg-blue-500/20',
    iconColor: 'text-blue-500',
    badgeColor: 'bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-500/30'
  },
  clarification: {
    label: 'Clarification',
    description: 'Clarification query templates',
    explanation: 'Generates targeted queries to verify source credibility, funding transparency, and author credentials for intelligence validation.',
    icon: MessageSquare,
    color: 'bg-purple-500',
    iconBgColor: 'bg-purple-500/10 dark:bg-purple-500/20',
    iconColor: 'text-purple-500',
    badgeColor: 'bg-purple-500/20 text-purple-700 dark:text-purple-400 border-purple-500/30'
  },
  evaluation: {
    label: 'Evaluation',
    description: 'Document evaluation templates',
    explanation: 'Assesses document value for wargaming scenarios, determining Signal/Review/Noise classification with confidence scoring.',
    icon: CheckSquare,
    color: 'bg-green-500',
    iconBgColor: 'bg-green-500/10 dark:bg-green-500/20',
    iconColor: 'text-green-500',
    badgeColor: 'bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/30'
  }
}

const PromptTemplateSection = ({
  type,
  templates,
  loading = false,
  onTest,
  onEdit,
  onDelete,
  onCompare,
  allTemplates = []
}) => {
  const config = PROMPT_TYPE_CONFIG[type] || PROMPT_TYPE_CONFIG.metadata
  const Icon = config.icon
  const typeTemplates = templates.filter(t => t.type === type)

  // Check if template can be compared (has other templates of same type)
  const canCompare = (template) => {
    return allTemplates.filter(t => t.type === template.type && t.id !== template.id).length > 0
  }

  return (
    <Card className="flex-1 flex flex-col min-h-0 min-w-0 border shadow-sm overflow-hidden">
      <CardHeader className="flex-shrink-0 pb-3 pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${config.iconBgColor}`}>
              <Icon className={`h-5 w-5 ${config.iconColor}`} />
            </div>
            <div>
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                {config.label}
                <Badge variant="outline" className={`${config.badgeColor} text-xs`}>
                  {typeTemplates.length}
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">
                {config.description}
              </CardDescription>
              <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                {config.explanation}
              </p>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0 p-0">
        {loading ? (
          <div className="flex items-center justify-center py-8 px-6">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Loading...</span>
          </div>
        ) : typeTemplates.length === 0 ? (
          <div className="text-center py-8 px-6">
            <Icon className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-50" />
            <p className="text-sm text-muted-foreground">No {config.label.toLowerCase()} templates</p>
          </div>
        ) : (
          <ScrollArea className="flex-1 min-h-0 px-4 pb-4">
            <div className="space-y-3 pt-2">
              {typeTemplates.map((template) => (
                <PromptTemplateCard
                  key={template.id}
                  template={template}
                  onTest={onTest}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onCompare={onCompare}
                  canCompare={canCompare(template)}
                />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}

export default PromptTemplateSection

