/**
 * Comprehensive Filter Component for Artifacts
 * 
 * Provides filtering by:
 * - Date ranges (created date, publication date)
 * - Document types (MIME types)
 * - Evaluation status (Signal, Review, Noise, Not Evaluated)
 * - Organization, Language, Topics, Geographic location, Authors
 * - Confidence score range
 * - Normalized content status
 * - Sort options
 */

import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Slider } from '@/components/ui/slider.jsx'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover.jsx'
import { Calendar } from '@/components/ui/calendar.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible.jsx'
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
import { Separator } from '@/components/ui/separator.jsx'

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

export default function ArtifactFilters({ 
  filters, 
  onFiltersChange,
  availableOrganizations = [],
  availableLanguages = [],
  availableTopics = [],
  availableGeoLocations = [],
  availableAuthors = []
}) {
  const [filtersOpen, setFiltersOpen] = useState(false)
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
    <div className="space-y-3">
      {/* Filter Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-sidebar-foreground/80" />
          <span className="text-xs font-medium text-sidebar-foreground/80">Filters</span>
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="h-5 px-1.5 text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </div>
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="h-6 px-2 text-xs text-sidebar-foreground/60 hover:text-sidebar-foreground"
          >
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Evaluation Status Filter */}
      <div className="space-y-2">
        <Label className="text-xs font-medium text-sidebar-foreground/80">Evaluation Status</Label>
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
              onClick={() => updateFilter('label', option.value)}
              className="h-7 px-2 text-xs"
            >
              {option.label}
            </Button>
          ))}
        </div>
      </div>


      {/* Document Type Filter */}
      <div className="space-y-2">
        <Label className="text-xs font-medium text-sidebar-foreground/80">Document Type</Label>
        <Select 
          value={filters.mime_type || "all"} 
          onValueChange={(value) => updateFilter('mime_type', value === "all" ? null : value)}
        >
          <SelectTrigger className="w-full h-8 text-xs">
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
        <Label className="text-xs font-medium text-sidebar-foreground/80">Retrieved Date Range</Label>
        <div className="grid grid-cols-2 gap-2">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm" className="h-8 text-xs justify-start">
                <CalendarIcon className="h-3 w-3 mr-1" />
                {filters.created_after ? format(new Date(filters.created_after), 'MMM dd') : 'From'}
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
              <Button variant="outline" size="sm" className="h-8 text-xs justify-start">
                <CalendarIcon className="h-3 w-3 mr-1" />
                {filters.created_before ? format(new Date(filters.created_before), 'MMM dd') : 'To'}
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

      {/* Sort Options */}
      <div className="space-y-2">
        <Label className="text-xs font-medium text-sidebar-foreground/80">Sort By</Label>
        <div className="flex items-center space-x-2">
          <Select 
            value={filters.sort_by || 'created_at'} 
            onValueChange={(value) => updateFilter('sort_by', value)}
          >
            <SelectTrigger className="flex-1 h-8 text-xs">
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
              const currentSort = SORT_OPTIONS.find(o => o.value === (filters.sort_by || 'created_at'))
              const currentOrder = filters.sort_order || 'desc'
              const newOrder = currentOrder === 'desc' ? 'asc' : 'desc'
              updateFilter('sort_order', newOrder)
            }}
            className="h-8 w-8 p-0"
          >
            {filters.sort_order === 'asc' ? (
              <SortAsc className="h-3 w-3" />
            ) : (
              <SortDesc className="h-3 w-3" />
            )}
          </Button>
        </div>
      </div>

      {/* Advanced Filters Collapsible */}
      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between h-8 text-xs">
            <span>Advanced Filters</span>
            {advancedOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-3 pt-2">
          {/* Organization Filter */}
          <div className="space-y-2">
            <Label className="text-xs font-medium text-sidebar-foreground/80">Organization</Label>
            <Input
              placeholder="Filter by organization..."
              value={filters.organization || ''}
              onChange={(e) => updateFilter('organization', e.target.value || null)}
              className="h-8 text-xs"
            />
          </div>

          {/* Language Filter */}
          <div className="space-y-2">
            <Label className="text-xs font-medium text-sidebar-foreground/80">Language</Label>
            <Select 
              value={filters.language || "all"} 
              onValueChange={(value) => updateFilter('language', value === "all" ? null : value)}
            >
              <SelectTrigger className="w-full h-8 text-xs">
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
            <Label className="text-xs font-medium text-sidebar-foreground/80">Topic</Label>
            <Input
              placeholder="Filter by topic..."
              value={filters.topic || ''}
              onChange={(e) => updateFilter('topic', e.target.value || null)}
              className="h-8 text-xs"
            />
          </div>

          {/* Geographic Location Filter */}
          <div className="space-y-2">
            <Label className="text-xs font-medium text-sidebar-foreground/80">Geographic Location</Label>
            <Input
              placeholder="Filter by location..."
              value={filters.geo_location || ''}
              onChange={(e) => updateFilter('geo_location', e.target.value || null)}
              className="h-8 text-xs"
            />
          </div>

          {/* Author Filter */}
          <div className="space-y-2">
            <Label className="text-xs font-medium text-sidebar-foreground/80">Author</Label>
            <Input
              placeholder="Filter by author..."
              value={filters.author || ''}
              onChange={(e) => updateFilter('author', e.target.value || null)}
              className="h-8 text-xs"
            />
          </div>

          {/* Confidence Range */}
          {(filters.min_confidence !== undefined || filters.max_confidence !== undefined) && (
            <div className="space-y-2">
              <Label className="text-xs font-medium text-sidebar-foreground/80">
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
                  className="h-8 text-xs"
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
                  className="h-8 text-xs"
                />
              </div>
            </div>
          )}

          {/* Has Normalized Content */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="has-normalized"
              checked={filters.has_normalized === true}
              onCheckedChange={(checked) => updateFilter('has_normalized', checked === true ? true : null)}
            />
            <Label htmlFor="has-normalized" className="text-xs font-normal cursor-pointer">
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
            <Label htmlFor="include-deleted-sources" className="text-xs font-normal cursor-pointer">
              Include artifacts from deleted sources
            </Label>
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Active Filter Badges */}
      {activeFilterCount > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-2 border-t border-sidebar-border">
          {filters.label && filters.label !== 'not_evaluated' && (
            <Badge variant="secondary" className="h-5 px-1.5 text-xs">
              {filters.label}
              <X className="h-3 w-3 ml-1 cursor-pointer" onClick={() => clearFilter('label')} />
            </Badge>
          )}
          {filters.label === 'not_evaluated' && (
            <Badge variant="secondary" className="h-5 px-1.5 text-xs">
              Not Evaluated
              <X className="h-3 w-3 ml-1 cursor-pointer" onClick={() => clearFilter('label')} />
            </Badge>
          )}
          {filters.mime_type && (
            <Badge variant="secondary" className="h-5 px-1.5 text-xs">
              {DOCUMENT_TYPES.find(t => t.value === filters.mime_type)?.label || filters.mime_type}
              <X className="h-3 w-3 ml-1 cursor-pointer" onClick={() => clearFilter('mime_type')} />
            </Badge>
          )}
          {filters.organization && (
            <Badge variant="secondary" className="h-5 px-1.5 text-xs">
              Org: {filters.organization.substring(0, 15)}
              <X className="h-3 w-3 ml-1 cursor-pointer" onClick={() => clearFilter('organization')} />
            </Badge>
          )}
          {/* Add more active filter badges as needed */}
        </div>
      )}
    </div>
  )
}

