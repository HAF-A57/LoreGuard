/**
 * ArtifactSidebar Component
 * Left sidebar containing search, filters, artifact list, and pagination
 */

import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { 
  Search, 
  FileText, 
  Filter,
  Trash2,
  ChevronsDownUp
} from 'lucide-react'
import { AnimatePresence } from 'framer-motion'
import ArtifactCard from './ArtifactCard.jsx'
import ArtifactPagination from './ArtifactPagination.jsx'
import { countActiveFilters } from '@/lib/artifacts/utils.js'

const ArtifactSidebar = ({
  searchQuery,
  onSearchChange,
  filters,
  onFiltersClick,
  onQuickFilterChange,
  artifacts,
  pagination,
  onPaginationChange,
  selectedArtifactIds,
  onToggleSelectAll,
  expandedArtifacts,
  expandAll,
  onToggleExpandAll,
  selectedArtifact,
  onArtifactClick,
  onToggleSelection,
  onToggleExpansion,
  evaluatingArtifacts,
  evaluationReadiness,
  onStartEvaluation,
  onDeleteClick,
  deleting
}) => {
  const activeFilterCount = countActiveFilters(filters)

  return (
    <aside className="w-80 bg-sidebar border-r border-sidebar-border flex flex-col flex-shrink-0 h-full overflow-hidden">
      {/* Header Section - Search and Filters */}
      <div className="p-4 pr-6 border-b border-sidebar-border space-y-3 flex-shrink-0">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-sidebar-foreground/60 dark:text-sidebar-foreground/60" />
          <Input
            placeholder="Search artifacts..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 text-sidebar-foreground placeholder:text-sidebar-foreground/60 bg-sidebar-accent/50 dark:bg-sidebar-accent/30 border-sidebar-border"
          />
        </div>
        
        {/* Filters Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={onFiltersClick}
          className="w-full justify-start"
        >
          <Filter className="h-4 w-4 mr-2" />
          Filters
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-auto h-5 px-1.5 text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
        
        {/* Quick Filter: Evaluation Status */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-sidebar-foreground/80">Quick Filter</label>
          <div className="flex flex-wrap gap-1.5">
            {[
              { value: null, label: 'All' },
              { value: 'Signal', label: 'Signal' },
              { value: 'Review', label: 'Review' },
              { value: 'Noise', label: 'Noise' },
              { value: 'not_evaluated', label: 'Not Evaluated' }
            ].map(option => (
              <Button
                key={option.value || 'all'}
                variant={filters.label === option.value ? "default" : "outline"}
                size="sm"
                onClick={() => onQuickFilterChange(option.value)}
                className="h-7 px-2 text-xs"
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Expand/Collapse All Toggle */}
        <div className="pt-2 border-t border-sidebar-border">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleExpandAll}
            className="w-full justify-start text-sidebar-foreground hover:text-sidebar-accent-foreground"
          >
            <ChevronsDownUp className="h-4 w-4 mr-2" />
            {expandAll ? 'Collapse All' : 'Expand All'}
          </Button>
        </div>
      </div>

      {/* Bulk Actions Toolbar */}
      {selectedArtifactIds.size > 0 && (
        <div className="p-4 border-b border-sidebar-border bg-sidebar-accent/50 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-sidebar-foreground">
              {selectedArtifactIds.size} selected
            </span>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => onDeleteClick(null)}
            disabled={deleting || evaluatingArtifacts.size > 0}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete Selected
          </Button>
        </div>
      )}

      {/* Artifact List */}
      <ScrollArea className="flex-1 min-h-0 overflow-hidden">
        <div
          className="p-3 pr-8 space-y-2 w-full min-w-0 box-border overflow-x-hidden break-words"
          style={{ overflowWrap: 'anywhere', maxWidth: 'calc(100% - 12px)' }}
        >
          {/* Pagination Info */}
          {artifacts.length > 0 && (
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-sidebar-border text-xs text-sidebar-foreground/60 min-w-0 pr-8">
              <span className="truncate">
                Showing {((pagination.currentPage - 1) * pagination.pageSize) + 1} - {Math.min(pagination.currentPage * pagination.pageSize, pagination.total)} of {pagination.total} artifacts
              </span>
              <Select
                value={String(pagination.pageSize)}
                onValueChange={(value) => {
                  onPaginationChange({ ...pagination, pageSize: parseInt(value), currentPage: 1 })
                }}
              >
                <SelectTrigger className="h-7 w-20 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="200">200</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
          
          {artifacts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No artifacts yet</p>
              <p className="text-xs mt-1">
                Run a crawl or create test artifacts
              </p>
            </div>
          ) : (
            <>
              {/* Select All */}
              <div className="flex items-center space-x-2 pb-2 mb-2 border-b border-sidebar-border min-w-0">
                <Checkbox
                  checked={selectedArtifactIds.size === artifacts.length && artifacts.length > 0}
                  onCheckedChange={onToggleSelectAll}
                  className="h-3.5 w-3.5"
                />
                <span className="text-xs text-sidebar-foreground/80 truncate">
                  Select All ({artifacts.length})
                </span>
              </div>
              
              {/* Artifact Cards */}
              <AnimatePresence mode="popLayout">
                {artifacts.map((artifact) => {
                  const hasEvaluation = artifact.label !== null
                  const isSelected = selectedArtifactIds.has(artifact.id)
                  const isExpanded = expandedArtifacts.has(artifact.id)
                  const isEvaluating = evaluatingArtifacts.has(artifact.id)
                  const readiness = evaluationReadiness[artifact.id]
                  const canEvaluate = !hasEvaluation && readiness?.ready === true
                  
                  return (
                    <ArtifactCard
                      key={artifact.id}
                      artifact={artifact}
                      isSelected={isSelected}
                      isExpanded={isExpanded}
                      isEvaluating={isEvaluating}
                      canEvaluate={canEvaluate}
                      isActiveArtifact={selectedArtifact?.id === artifact.id}
                      onSelect={() => onToggleSelection(artifact.id)}
                      onToggleExpansion={() => onToggleExpansion(artifact.id)}
                      onEvaluate={onStartEvaluation}
                      onDelete={onDeleteClick}
                      onCardClick={() => !isEvaluating && onArtifactClick(artifact)}
                    />
                  )
                })}
              </AnimatePresence>
              
              {/* Pagination Controls */}
              {pagination.totalPages > 1 && (
                <div className="min-w-0 w-full max-w-full pr-8">
                  <ArtifactPagination
                    pagination={pagination}
                    onPageChange={(page) => onPaginationChange({ ...pagination, currentPage: page })}
                  />
                </div>
              )}
            </>
          )}
        </div>
      </ScrollArea>
    </aside>
  )
}

export default ArtifactSidebar

