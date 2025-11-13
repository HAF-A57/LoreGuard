/**
 * Artifacts Component
 * Main page for browsing, filtering, and managing artifacts
 * Refactored to use custom hooks and sub-components for better maintainability
 */

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Loader2, AlertCircle } from 'lucide-react'
import { API_URL } from '@/config.js'
import ArtifactFiltersModal from '@/components/ArtifactFiltersModal.jsx'
import ArtifactSidebar from '@/components/artifacts/ArtifactSidebar.jsx'
import ArtifactDetailView from '@/components/artifacts/ArtifactDetailView.jsx'
import ArtifactDeleteDialog from '@/components/artifacts/ArtifactDeleteDialog.jsx'
import ArtifactEvaluationDialog from '@/components/artifacts/ArtifactEvaluationDialog.jsx'
import { useArtifactsData } from '@/lib/artifacts/hooks/useArtifactsData.js'
import { useEvaluationJob } from '@/lib/artifacts/hooks/useEvaluationJob.js'
import { useArtifactDeletion } from '@/lib/artifacts/hooks/useArtifactDeletion.js'
import { useArtifactSelection } from '@/lib/artifacts/hooks/useArtifactSelection.js'
import { useDebounce } from '@/lib/hooks/useDebounce.js'

const Artifacts = () => {
  // Selected artifact state (for detail view)
  const [selectedArtifact, setSelectedArtifact] = useState(null)
  const [selectedArtifactDetails, setSelectedArtifactDetails] = useState(null)
  const [normalizedContent, setNormalizedContent] = useState(null)
  const [evaluations, setEvaluations] = useState([])
  const [contentLoading, setContentLoading] = useState(false)
  const [contentError, setContentError] = useState(null)
  const [evaluationsLoading, setEvaluationsLoading] = useState(false)
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState("")
  const [localSearchQuery, setLocalSearchQuery] = useState("") // Local state for immediate UI updates
  const debouncedSearchQuery = useDebounce(localSearchQuery, 400) // Debounced value for API calls
  
  // Sync debounced search query to actual search query
  useEffect(() => {
    setSearchQuery(debouncedSearchQuery)
    // Reset to first page when search changes
    setPagination(prev => ({ ...prev, currentPage: 1 }))
  }, [debouncedSearchQuery])
  
  const [filters, setFilters] = useState({
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
  const [filtersModalOpen, setFiltersModalOpen] = useState(false)
  
  // Pagination state
  const [pagination, setPagination] = useState({
    currentPage: 1,
    pageSize: 50,
    total: 0,
    totalPages: 0
  })
  
  // Sources for filter dropdown
  const [sources, setSources] = useState([])

  // Custom hooks for data and operations
  const { artifacts, loading, error, evaluationReadiness, refreshArtifacts } = useArtifactsData(
    filters,
    pagination,
    searchQuery,
    (total) => {
      // Update pagination total when data is fetched
      const totalPages = Math.ceil(total / pagination.pageSize) || 1
      setPagination(prev => ({ ...prev, total, totalPages }))
    }
  )

  const {
    evaluationTarget,
    evaluatingArtifacts,
    startEvaluation,
    openEvaluationDialog,
    closeEvaluationDialog
  } = useEvaluationJob(async (artifactId) => {
    // Callback after evaluation completes - refresh data
    await refreshArtifacts()
    // Refresh selected artifact details if it was the one evaluated
    if (selectedArtifact && selectedArtifact.id === artifactId) {
      const updatedArtifact = artifacts.find(a => a.id === artifactId)
      if (updatedArtifact) {
        setSelectedArtifact(updatedArtifact)
        await fetchArtifactDetails(updatedArtifact)
      }
    }
  })

  const {
    deleteDialogOpen,
    deleteTarget,
    deleting,
    openDeleteDialog,
    closeDeleteDialog,
    executeDelete
  } = useArtifactDeletion(async (artifactId) => {
    // Callback after deletion - refresh and clear selections
    await refreshArtifacts()
    
    if (artifactId) {
      // Single delete - clear selection if it was selected
      if (selectedArtifact?.id === artifactId) {
        setSelectedArtifact(null)
      }
      clearSelections()
    } else {
      // Bulk delete - clear all selections
      clearSelections()
      if (selectedArtifact && selectedArtifactIds.has(selectedArtifact.id)) {
        setSelectedArtifact(null)
      }
    }
  })

  const {
    selectedArtifactIds,
    expandedArtifacts,
    expandAll,
    toggleArtifactSelection,
    toggleSelectAll,
    clearSelections,
    toggleArtifactExpansion,
    toggleExpandAll
  } = useArtifactSelection(artifacts)

  // Fetch sources for filter dropdown
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/sources/`)
        if (response.ok) {
          const data = await response.json()
          setSources(data.items || [])
        }
      } catch (err) {
        console.error('Error fetching sources:', err)
      }
    }
    fetchSources()
  }, [])

  // Fetch full artifact details when selected
  const fetchArtifactDetails = async (artifact) => {
    if (!artifact) {
      setSelectedArtifactDetails(null)
      setNormalizedContent(null)
      setEvaluations([])
      return
    }

    try {
      // Fetch full artifact details
      const artifactResponse = await fetch(`${API_URL}/api/v1/artifacts/${artifact.id}`)
      if (!artifactResponse.ok) throw new Error('Failed to fetch artifact details')
      const artifactData = await artifactResponse.json()
      setSelectedArtifactDetails(artifactData)

      // Fetch normalized content
      setContentLoading(true)
      setContentError(null)
      try {
        const contentResponse = await fetch(`${API_URL}/api/v1/artifacts/${artifact.id}/normalized-content`)
        if (contentResponse.ok) {
          const contentData = await contentResponse.json()
          setNormalizedContent(contentData.content)
        } else if (contentResponse.status === 404) {
          setNormalizedContent(null)
          setContentError('Artifact has not been normalized yet')
        } else {
          throw new Error('Failed to fetch normalized content')
        }
      } catch (err) {
        console.error('Error fetching normalized content:', err)
        setContentError(err.message)
        setNormalizedContent(null)
      } finally {
        setContentLoading(false)
      }

      // Fetch evaluations with full details
      setEvaluationsLoading(true)
      try {
        const evaluationsResponse = await fetch(`${API_URL}/api/v1/artifacts/${artifact.id}/evaluations`)
        if (evaluationsResponse.ok) {
          const evaluationsData = await evaluationsResponse.json()
          setEvaluations(evaluationsData.evaluations || [])
        } else {
          setEvaluations([])
        }
      } catch (err) {
        console.error('Error fetching evaluations:', err)
        setEvaluations([])
      } finally {
        setEvaluationsLoading(false)
      }
    } catch (err) {
      console.error('Error fetching artifact details:', err)
      setSelectedArtifactDetails(null)
    }
  }

  // Handle artifact selection change
  useEffect(() => {
    fetchArtifactDetails(selectedArtifact)
  }, [selectedArtifact])

  // Handle navigation from Dashboard (via localStorage)
  useEffect(() => {
    const navigateToArtifactId = localStorage.getItem('loreguard_navigate_to_artifact')
    if (navigateToArtifactId && artifacts.length > 0) {
      const targetArtifact = artifacts.find(a => a.id === navigateToArtifactId)
      if (targetArtifact) {
        localStorage.removeItem('loreguard_navigate_to_artifact')
        setTimeout(() => {
          setSelectedArtifact(targetArtifact)
        }, 100)
      }
    }
  }, [artifacts])

  // Loading state
  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading artifacts...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <span>Error Loading Artifacts</span>
            </CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden">
      {/* Sidebar with artifact list */}
      <ArtifactSidebar
        searchQuery={localSearchQuery}
        onSearchChange={setLocalSearchQuery}
        filters={filters}
        onFiltersClick={() => setFiltersModalOpen(true)}
        onQuickFilterChange={(label) => {
          setFilters(prev => ({ ...prev, label }))
          setPagination(prev => ({ ...prev, currentPage: 1 }))
        }}
        artifacts={artifacts}
        pagination={pagination}
        onPaginationChange={setPagination}
        selectedArtifactIds={selectedArtifactIds}
        onToggleSelectAll={toggleSelectAll}
        expandedArtifacts={expandedArtifacts}
        expandAll={expandAll}
        onToggleExpandAll={toggleExpandAll}
        selectedArtifact={selectedArtifact}
        onArtifactClick={setSelectedArtifact}
        onToggleSelection={toggleArtifactSelection}
        onToggleExpansion={toggleArtifactExpansion}
        evaluatingArtifacts={evaluatingArtifacts}
        evaluationReadiness={evaluationReadiness}
        onStartEvaluation={openEvaluationDialog}
        onDeleteClick={openDeleteDialog}
        deleting={deleting}
      />

      {/* Main content with artifact details */}
      <ArtifactDetailView
        selectedArtifact={selectedArtifact}
        selectedArtifactDetails={selectedArtifactDetails}
        normalizedContent={normalizedContent}
        contentLoading={contentLoading}
        contentError={contentError}
        evaluations={evaluations}
        evaluationsLoading={evaluationsLoading}
        evaluationReadiness={evaluationReadiness}
        evaluatingArtifacts={evaluatingArtifacts}
        onStartEvaluation={openEvaluationDialog}
      />

      {/* Filters Modal */}
      <ArtifactFiltersModal
        open={filtersModalOpen}
        onOpenChange={setFiltersModalOpen}
        filters={filters}
        onFiltersChange={(newFilters) => {
          setFilters(newFilters)
          setPagination(prev => ({ ...prev, currentPage: 1 }))
        }}
        sources={sources}
        availableOrganizations={[]}
        availableLanguages={[]}
        availableTopics={[]}
        availableGeoLocations={[]}
        availableAuthors={[]}
      />

      {/* Delete Confirmation Dialog */}
      <ArtifactDeleteDialog
        open={deleteDialogOpen}
        onOpenChange={closeDeleteDialog}
        deleteTarget={deleteTarget}
        selectedCount={selectedArtifactIds.size}
        deleting={deleting}
        onConfirm={() => executeDelete(
          deleteTarget === 'bulk' ? null : deleteTarget,
          selectedArtifactIds
        )}
      />

      {/* Evaluation Dialog */}
      <ArtifactEvaluationDialog
        open={!!evaluationTarget}
        onOpenChange={(open) => {
          if (!open) closeEvaluationDialog()
        }}
        evaluationTarget={evaluationTarget}
        evaluationReadiness={evaluationReadiness}
        onEvaluate={startEvaluation}
      />
    </div>
  )
}

export default Artifacts
