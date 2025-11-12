/**
 * Filter Modal Component for Artifacts
 * 
 * Provides comprehensive filtering in a modal dialog
 */

import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover.jsx'
import { Calendar } from '@/components/ui/calendar.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog.jsx'
import { 
  Filter, 
  X, 
  ChevronDown, 
  ChevronUp,
  Calendar as CalendarIcon,
  FileType,
  Globe,
  Users,
  MapPin,
  Tag,
  TrendingUp,
  SortAsc,
  SortDesc
} from 'lucide-react'
import { format } from 'date-fns'

const DOCUMENT_TYPES = [
  { value: 'application/pdf', label: 'PDF', icon: FileType },
  { value: 'text/html', label: 'HTML/Web', icon: Globe },
  { value: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', label: 'DOCX', icon: FileType },
  { value: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', label: 'PPTX', icon: FileType },
  { value: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', label: 'XLSX', icon: FileType },
  { value: 'text/plain', label: 'TXT', icon: FileType },
]

const SORT_OPTIONS = [
  { value: 'created_at', label: 'Date Retrieved', fields: ['desc', 'asc'] },
  { value: 'title', label: 'Title', fields: ['asc', 'desc'] },
  { value: 'confidence', label: 'Evaluation Score', fields: ['desc', 'asc'] },
  { value: 'pub_date', label: 'Publication Date', fields: ['desc', 'asc'] },
]

export default function ArtifactFiltersModal({ 
  open,
  onOpenChange,
  filters, 
  onFiltersChange,
  sources = [],
  availableOrganizations = [],
  availableLanguages = [],
  availableTopics = [],
  availableGeoLocations = [],
  availableAuthors = []
}) {
  const [advancedOpen, setAdvancedOpen] = useState(false)

  const updateFilter = (key, value) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const clearFilter = (key) => {
    const newFilters = { ...filters }
    delete newFilters[key]
    onFiltersChange(newFilters)
  }

  const clearAllFilters = () => {
    onFiltersChange({
      label: null,
      source_id: null,
      include_deleted_sources: true,
      mime_type: null,
      created_after: null,
      created_before: null,
      pub_date_after: null,
      pub_date_before: null,
      organization: null,
      language: null,
      topic: null,
      geo_location: null,
      author: null,
      min_confidence: null,
      max_confidence: null,
      has_normalized: null,
      sort_by: 'created_at',
      sort_order: 'desc',
      limit: 50,
      skip: 0
    })
  }

  const activeFilterCount = Object.keys(filters).filter(key => {
    const value = filters[key]
    if (key === 'include_deleted_sources') return false // Don't count default
    if (key === 'sort_by' && value === 'created_at') return false // Don't count default
    if (key === 'sort_order' && value === 'desc') return false // Don't count default
    if (key === 'limit' && value === 50) return false // Don't count default
    if (key === 'skip' && value === 0) return false // Don't count default
    return value !== null && value !== undefined && value !== ''
  }).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 flex-shrink-0">
          <DialogTitle className="flex items-center space-x-2">
            <Filter className="h-5 w-5" />
            <span>Filter Artifacts</span>
            {activeFilterCount > 0 && (
              <Badge variant="secondary" className="ml-2">
                {activeFilterCount} active
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            Use filters to narrow down your artifact search
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 min-h-0 px-6">
          <div className="py-4">
            <div className="space-y-6">
            {/* Evaluation Status Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-semibold">Evaluation Status</Label>
              <div className="flex flex-wrap gap-2">
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
                    onClick={() => updateFilter('label', option.value)}
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
            </div>

            <Separator />

            {/* Source Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-semibold">Source</Label>
              <Select 
                value={filters.source_id || "all"} 
                onValueChange={(value) => updateFilter('source_id', value === "all" ? null : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Sources" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sources</SelectItem>
                  {sources.map((source) => (
                    <SelectItem key={source.id} value={source.id}>
                      {source.name} ({source.document_count || 0})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Document Type Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-semibold">Document Type</Label>
              <Select 
                value={filters.mime_type || "all"} 
                onValueChange={(value) => updateFilter('mime_type', value === "all" ? null : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {DOCUMENT_TYPES.map(type => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Date Range Filters */}
            <div className="space-y-2">
              <Label className="text-sm font-semibold">Retrieved Date Range</Label>
              <div className="grid grid-cols-2 gap-2">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" size="sm" className="justify-start">
                      <CalendarIcon className="h-4 w-4 mr-2" />
                      {filters.created_after ? format(new Date(filters.created_after), 'MMM dd, yyyy') : 'From'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.created_after ? new Date(filters.created_after) : undefined}
                      onSelect={(date) => updateFilter('created_after', date ? format(date, 'yyyy-MM-dd') : null)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" size="sm" className="justify-start">
                      <CalendarIcon className="h-4 w-4 mr-2" />
                      {filters.created_before ? format(new Date(filters.created_before), 'MMM dd, yyyy') : 'To'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.created_before ? new Date(filters.created_before) : undefined}
                      onSelect={(date) => updateFilter('created_before', date ? format(date, 'yyyy-MM-dd') : null)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            {/* Publication Date Range */}
            <div className="space-y-2">
              <Label className="text-sm font-semibold">Publication Date Range</Label>
              <div className="grid grid-cols-2 gap-2">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" size="sm" className="justify-start">
                      <CalendarIcon className="h-4 w-4 mr-2" />
                      {filters.pub_date_after ? format(new Date(filters.pub_date_after), 'MMM dd, yyyy') : 'From'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.pub_date_after ? new Date(filters.pub_date_after) : undefined}
                      onSelect={(date) => updateFilter('pub_date_after', date ? format(date, 'yyyy-MM-dd') : null)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" size="sm" className="justify-start">
                      <CalendarIcon className="h-4 w-4 mr-2" />
                      {filters.pub_date_before ? format(new Date(filters.pub_date_before), 'MMM dd, yyyy') : 'To'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.pub_date_before ? new Date(filters.pub_date_before) : undefined}
                      onSelect={(date) => updateFilter('pub_date_before', date ? format(date, 'yyyy-MM-dd') : null)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            {/* Sort Options */}
            <div className="space-y-2">
              <Label className="text-sm font-semibold">Sort By</Label>
              <div className="flex items-center space-x-2">
                <Select 
                  value={filters.sort_by || 'created_at'} 
                  onValueChange={(value) => updateFilter('sort_by', value)}
                  className="flex-1"
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SORT_OPTIONS.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const currentOrder = filters.sort_order || 'desc'
                    const newOrder = currentOrder === 'desc' ? 'asc' : 'desc'
                    updateFilter('sort_order', newOrder)
                  }}
                  className="w-10 p-0"
                >
                  {filters.sort_order === 'asc' ? (
                    <SortAsc className="h-4 w-4" />
                  ) : (
                    <SortDesc className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <Separator />

            {/* Advanced Filters Collapsible */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-semibold">Advanced Filters</Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setAdvancedOpen(!advancedOpen)}
                >
                  {advancedOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </Button>
              </div>

              {advancedOpen && (
                <div className="space-y-4 pl-4 border-l-2 border-border">
                  {/* Organization Filter */}
                  <div className="space-y-2">
                    <Label>Organization</Label>
                    <Input
                      placeholder="Filter by organization..."
                      value={filters.organization || ''}
                      onChange={(e) => updateFilter('organization', e.target.value || null)}
                    />
                  </div>

                  {/* Language Filter */}
                  <div className="space-y-2">
                    <Label>Language</Label>
                    <Select 
                      value={filters.language || "all"} 
                      onValueChange={(value) => updateFilter('language', value === "all" ? null : value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All Languages" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Languages</SelectItem>
                        {availableLanguages.map(lang => (
                          <SelectItem key={lang} value={lang}>
                            {lang.toUpperCase()}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Topic Filter */}
                  <div className="space-y-2">
                    <Label>Topic</Label>
                    <Input
                      placeholder="Filter by topic..."
                      value={filters.topic || ''}
                      onChange={(e) => updateFilter('topic', e.target.value || null)}
                    />
                  </div>

                  {/* Geographic Location Filter */}
                  <div className="space-y-2">
                    <Label>Geographic Location</Label>
                    <Input
                      placeholder="Filter by location..."
                      value={filters.geo_location || ''}
                      onChange={(e) => updateFilter('geo_location', e.target.value || null)}
                    />
                  </div>

                  {/* Author Filter */}
                  <div className="space-y-2">
                    <Label>Author</Label>
                    <Input
                      placeholder="Filter by author..."
                      value={filters.author || ''}
                      onChange={(e) => updateFilter('author', e.target.value || null)}
                    />
                  </div>

                  {/* Confidence Range */}
                  <div className="space-y-2">
                    <Label>
                      Confidence Score: {filters.min_confidence !== undefined ? Math.round(filters.min_confidence * 100) : 0}% - {filters.max_confidence !== undefined ? Math.round(filters.max_confidence * 100) : 100}%
                    </Label>
                    <div className="grid grid-cols-2 gap-2">
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        placeholder="Min %"
                        value={filters.min_confidence !== undefined ? Math.round(filters.min_confidence * 100) : ''}
                        onChange={(e) => {
                          const value = e.target.value ? parseFloat(e.target.value) / 100 : null
                          updateFilter('min_confidence', value)
                        }}
                      />
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        placeholder="Max %"
                        value={filters.max_confidence !== undefined ? Math.round(filters.max_confidence * 100) : ''}
                        onChange={(e) => {
                          const value = e.target.value ? parseFloat(e.target.value) / 100 : null
                          updateFilter('max_confidence', value)
                        }}
                      />
                    </div>
                  </div>

                  {/* Has Normalized Content */}
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="has-normalized"
                      checked={filters.has_normalized === true}
                      onCheckedChange={(checked) => updateFilter('has_normalized', checked === true ? true : null)}
                    />
                    <Label htmlFor="has-normalized" className="cursor-pointer">
                      Has normalized content only
                    </Label>
                  </div>

                  {/* Include Deleted Sources */}
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="include-deleted-sources"
                      checked={filters.include_deleted_sources !== false}
                      onCheckedChange={(checked) => updateFilter('include_deleted_sources', checked === true)}
                    />
                    <Label htmlFor="include-deleted-sources" className="cursor-pointer">
                      Include artifacts from deleted sources
                    </Label>
                  </div>
                </div>
              )}
            </div>

            {/* Active Filter Badges */}
            {activeFilterCount > 0 && (
              <div className="space-y-2">
                <Label className="text-sm font-semibold">Active Filters</Label>
                <div className="flex flex-wrap gap-2">
                  {filters.label && filters.label !== 'not_evaluated' && (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      {filters.label}
                      <X className="h-3 w-3 cursor-pointer" onClick={() => clearFilter('label')} />
                    </Badge>
                  )}
                  {filters.label === 'not_evaluated' && (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      Not Evaluated
                      <X className="h-3 w-3 cursor-pointer" onClick={() => clearFilter('label')} />
                    </Badge>
                  )}
                  {filters.mime_type && (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      {DOCUMENT_TYPES.find(t => t.value === filters.mime_type)?.label || filters.mime_type}
                      <X className="h-3 w-3 cursor-pointer" onClick={() => clearFilter('mime_type')} />
                    </Badge>
                  )}
                  {filters.source_id && (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      Source: {sources.find(s => s.id === filters.source_id)?.name || filters.source_id.substring(0, 8)}
                      <X className="h-3 w-3 cursor-pointer" onClick={() => clearFilter('source_id')} />
                    </Badge>
                  )}
                  {filters.organization && (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      Org: {filters.organization.substring(0, 15)}
                      <X className="h-3 w-3 cursor-pointer" onClick={() => clearFilter('organization')} />
                    </Badge>
                  )}
                  {filters.created_after && (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      From: {format(new Date(filters.created_after), 'MMM dd')}
                      <X className="h-3 w-3 cursor-pointer" onClick={() => clearFilter('created_after')} />
                    </Badge>
                  )}
                  {filters.created_before && (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      To: {format(new Date(filters.created_before), 'MMM dd')}
                      <X className="h-3 w-3 cursor-pointer" onClick={() => clearFilter('created_before')} />
                    </Badge>
                  )}
                  {/* Add more active filter badges as needed */}
                </div>
              </div>
            )}
            </div>
          </div>
        </ScrollArea>

        <DialogFooter className="px-6 pb-6 pt-4 flex-shrink-0 border-t">
          <Button variant="outline" onClick={clearAllFilters} disabled={activeFilterCount === 0}>
            Clear All
          </Button>
          <Button onClick={() => onOpenChange(false)}>
            Apply Filters
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

