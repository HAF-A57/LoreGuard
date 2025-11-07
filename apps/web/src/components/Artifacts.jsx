import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Search, 
  Filter, 
  FileText, 
  Globe, 
  Clock, 
  Star, 
  Eye,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { API_URL } from '@/config.js'

const Artifacts = () => {
  const [selectedArtifact, setSelectedArtifact] = useState(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [artifacts, setArtifacts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [labelFilter, setLabelFilter] = useState(null) // null, 'Signal', 'Review', 'Noise'

  // Fetch artifacts with evaluations
  useEffect(() => {
    const fetchArtifacts = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch artifacts with metadata
        const artifactsResponse = await fetch(`${API_URL}/api/v1/artifacts/?limit=100`)
        if (!artifactsResponse.ok) throw new Error('Failed to fetch artifacts')
        const artifactsData = await artifactsResponse.json()
        const artifactsList = artifactsData.items || []

        // Fetch evaluations to get labels and confidence
        const evaluationsResponse = await fetch(`${API_URL}/api/v1/evaluations/?limit=1000`)
        const evaluationsData = await evaluationsResponse.ok ? await evaluationsResponse.json() : { items: [] }
        const evaluations = evaluationsData.items || []

        // Create evaluation map for quick lookup
        const evalMap = {}
        evaluations.forEach(ev => {
          if (ev.artifact_id && !evalMap[ev.artifact_id]) {
            evalMap[ev.artifact_id] = ev
          }
        })

        // Enrich artifacts with evaluation data
        const enrichedArtifacts = artifactsList.map(artifact => {
          const evaluation = evalMap[artifact.id]
          return {
            ...artifact,
            label: evaluation?.label || null,
            confidence: evaluation?.confidence || null,
            title: artifact.title || `Artifact ${artifact.id.substring(0, 8)}`,
            source: artifact.organization || 'Unknown Source',
            date: artifact.created_at ? new Date(artifact.created_at).toLocaleDateString() : 'Unknown',
            topics: artifact.topics || [],
            summary: `URI: ${artifact.uri}` // Placeholder summary
          }
        })

        setArtifacts(enrichedArtifacts)
      } catch (err) {
        console.error('Error fetching artifacts:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchArtifacts()
  }, [])

  const filteredArtifacts = artifacts.filter(artifact => {
    const matchesSearch = !searchQuery || 
      artifact.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      artifact.uri?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (artifact.topics && artifact.topics.some(topic => topic.toLowerCase().includes(searchQuery.toLowerCase())))
    
    const matchesLabel = !labelFilter || artifact.label === labelFilter
    
    return matchesSearch && matchesLabel
  })

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
    <div className="min-h-[calc(100vh-4rem)] flex">
      {/* Sidebar */}
      <aside className="w-80 bg-sidebar border-r border-sidebar-border flex flex-col flex-shrink-0 relative">
        <div className="p-4 border-b border-sidebar-border space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search artifacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          {/* Label Filter Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant={labelFilter === null ? "default" : "outline"}
              size="sm"
              onClick={() => setLabelFilter(null)}
            >
              All
            </Button>
            <Button
              variant={labelFilter === 'Signal' ? "default" : "outline"}
              size="sm"
              onClick={() => setLabelFilter('Signal')}
            >
              Signal
            </Button>
            <Button
              variant={labelFilter === 'Review' ? "default" : "outline"}
              size="sm"
              onClick={() => setLabelFilter('Review')}
            >
              Review
            </Button>
            <Button
              variant={labelFilter === 'Noise' ? "default" : "outline"}
              size="sm"
              onClick={() => setLabelFilter('Noise')}
            >
              Noise
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4 space-y-3">
            {filteredArtifacts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>{artifacts.length === 0 ? 'No artifacts yet' : 'No matching artifacts'}</p>
                <p className="text-xs mt-1">
                  {artifacts.length === 0 
                    ? 'Run a crawl or create test artifacts' 
                    : 'Try adjusting your search or filters'}
                </p>
              </div>
            ) : (
              filteredArtifacts.map((artifact) => {
                const hasEvaluation = artifact.label !== null
                const confidence = artifact.confidence ? parseFloat(artifact.confidence) : 0
                
                return (
                  <Card
                    key={artifact.id}
                    className={`cursor-pointer aulendur-hover-transform transition-all ${
                      selectedArtifact?.id === artifact.id ? 'ring-2 ring-primary' : ''
                    }`}
                    onClick={() => setSelectedArtifact(artifact)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        {hasEvaluation ? (
                          <Badge variant={
                            artifact.label === 'Signal' ? 'default' : 
                            artifact.label === 'Review' ? 'secondary' : 'outline'
                          }>
                            {artifact.label}
                          </Badge>
                        ) : (
                          <Badge variant="outline">Not Evaluated</Badge>
                        )}
                        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{artifact.date}</span>
                        </div>
                      </div>
                      <CardTitle className="text-sm line-clamp-2">{artifact.title}</CardTitle>
                      <CardDescription className="text-xs">{artifact.source}</CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                      {hasEvaluation && (
                        <>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-muted-foreground">Confidence</span>
                            <span className="text-xs font-medium">{Math.round(confidence * 100)}%</span>
                          </div>
                          <Progress value={confidence * 100} className="h-1 mb-2" />
                        </>
                      )}
                      {artifact.topics && artifact.topics.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {artifact.topics.slice(0, 2).map((topic, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                          {artifact.topics.length > 2 && (
                            <Badge variant="outline" className="text-xs">
                              +{artifact.topics.length - 2}
                            </Badge>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })
            )}
          </div>
        </ScrollArea>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-0">
        {selectedArtifact ? (
          <>
            {/* Content Header */}
            <div className="p-6 border-b border-border bg-card">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant={selectedArtifact.label === 'Signal' ? 'default' : 'secondary'}>
                      {selectedArtifact.label}
                    </Badge>
                    <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      <span>{selectedArtifact.date}</span>
                    </div>
                  </div>
                  <h2 className="text-2xl font-bold mb-2">{selectedArtifact.title}</h2>
                  <p className="text-muted-foreground mb-3">{selectedArtifact.source}</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedArtifact.topics.map((topic) => (
                      <Badge key={topic} variant="outline">
                        {topic}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-6">
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">Confidence Score</div>
                    <div className="text-2xl font-bold text-primary">
                      {(selectedArtifact.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </Button>
                </div>
              </div>
            </div>

            {/* Content Body */}
            <div className="flex-1 p-6 overflow-auto">
              <Card className="aulendur-gradient-card">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <FileText className="h-5 w-5" />
                    <span>Artifact Summary</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-foreground leading-relaxed mb-6">
                    {selectedArtifact.summary}
                  </p>
                  
                  <Separator className="my-6" />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center space-x-2">
                        <Star className="h-4 w-4" />
                        <span>Key Insights</span>
                      </h4>
                      <ul className="space-y-2 text-sm text-muted-foreground">
                        <li>• Strategic implications for regional security</li>
                        <li>• Economic impact assessment methodology</li>
                        <li>• Recommended policy adjustments</li>
                        <li>• Timeline for implementation</li>
                      </ul>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center space-x-2">
                        <Globe className="h-4 w-4" />
                        <span>Geographic Scope</span>
                      </h4>
                      <ul className="space-y-2 text-sm text-muted-foreground">
                        <li>• Primary: Eastern Europe</li>
                        <li>• Secondary: NATO Member States</li>
                        <li>• Tertiary: Global Supply Networks</li>
                        <li>• Focus: Strategic Corridors</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Select an Artifact</h3>
              <p className="text-muted-foreground">Choose an artifact from the sidebar to view its details</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default Artifacts

