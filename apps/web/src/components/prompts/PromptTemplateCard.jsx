/**
 * PromptTemplateCard Component
 * Reusable card component for displaying individual prompt templates
 */

import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Play, Edit, Trash2, GitCompare } from 'lucide-react'

const PromptTemplateCard = ({
  template,
  onTest,
  onEdit,
  onDelete,
  onCompare,
  canCompare = false
}) => {
  const getTypeColor = (type) => {
    switch (type) {
      case 'metadata': return 'bg-blue-500'
      case 'evaluation': return 'bg-green-500'
      case 'clarification': return 'bg-purple-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <Card 
      className={`lgcustom-hover-transform ${
        template.is_default 
          ? 'border-2 border-primary shadow-lg bg-primary/5 dark:bg-primary/10' 
          : ''
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2 flex-wrap gap-2">
              <span className="font-medium">{template.name}</span>
              <Badge className={getTypeColor(template.type)}>
                {template.type}
              </Badge>
              {template.is_default && (
                <Badge variant="default" className="font-semibold">Default</Badge>
              )}
              {template.is_active ? (
                <Badge variant="default" className="bg-green-500">Active</Badge>
              ) : (
                <Badge variant="secondary">Inactive</Badge>
              )}
              <Badge variant="outline">v{template.version}</Badge>
            </div>
            <div className="text-sm text-muted-foreground mb-2">
              Reference ID: <code className="text-xs bg-muted px-1 py-0.5 rounded">{template.reference_id}</code>
            </div>
            {template.description && (
              <p className="text-sm text-muted-foreground mb-2">{template.description}</p>
            )}
            <div className="flex items-center space-x-4 text-xs text-muted-foreground">
              <span>Used {template.usage_count || 0} times</span>
              <span>•</span>
              <span>Created {new Date(template.created_at).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="flex items-center space-x-2 ml-4">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onTest(template)}
              title="Test Template"
            >
              <Play className="h-4 w-4" />
            </Button>
            {canCompare && (
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => onCompare(template)}
                title="Compare Versions"
              >
                <GitCompare className="h-4 w-4" />
              </Button>
            )}
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onEdit(template)}
              title="Edit Template"
            >
              <Edit className="h-4 w-4" />
            </Button>
            {!template.is_default && (
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => onDelete(template)}
                title="Delete Template"
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default PromptTemplateCard

