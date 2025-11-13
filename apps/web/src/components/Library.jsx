import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { 
  Search, 
  Filter, 
  Download, 
  Share, 
  BookOpen, 
  Star, 
  Calendar,
  Tag,
  ExternalLink,
  Archive,
  Trash2,
  Plus,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { API_URL } from '@/config.js'

const Library = () => {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedItems, setSelectedItems] = useState([])
  const [libraryItems, setLibraryItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch Signal artifacts from library endpoint
  useEffect(() => {
    const fetchLibrary = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch library items (Signal artifacts)
        const response = await fetch(`${API_URL}/api/v1/library/?limit=100`)
        if (!response.ok) throw new Error('Failed to fetch library')
        const data = await response.json()
        const items = data.items || []

        // Enrich with evaluation data
        const enrichedItems = items.map(item => ({
          id: item.id,
          title: item.title || `Artifact ${item.id.substring(0, 8)}`,
          source: item.organization || 'Unknown Source',
          dateAdded: item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Unknown',
          confidence: item.confidence || 0,
          tags: item.topics || [],
          summary: item.uri || 'No summary available',
          category: "Defense",  // Placeholder
          priority: item.confidence > 0.85 ? "High" : "Medium"
        }))

        setLibraryItems(enrichedItems)
      } catch (err) {
        console.error('Error fetching library:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchLibrary()
  }, [])

  const filteredItems = libraryItems.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.tags.some(tag => tag && tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const toggleSelection = (itemId) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    )
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading Signal library...</p>
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
              <span>Error Loading Library</span>
            </CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">Signal Library</h1>
            <p className="text-muted-foreground">Curated high-value artifacts for distribution</p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Archive className="h-4 w-4 mr-2" />
              Export Selected<span className="placeholder-indicator">⭐</span>
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add to Library<span className="placeholder-indicator">⭐</span>
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center space-x-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search library items..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filters<span className="placeholder-indicator">⭐</span>
          </Button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="p-4 bg-muted/30 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <BookOpen className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">{filteredItems.length} Items</span>
            </div>
            <div className="flex items-center space-x-2">
              <Star className="h-4 w-4 text-yellow-500" />
              <span className="text-sm font-medium">{filteredItems.filter(item => item.priority === 'High').length} High Priority</span>
            </div>
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Last updated today</span>
            </div>
          </div>
          {selectedItems.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">{selectedItems.length} selected</span>
              <Button variant="outline" size="sm">
                <Share className="h-4 w-4 mr-2" />
                Share<span className="placeholder-indicator">⭐</span>
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download<span className="placeholder-indicator">⭐</span>
              </Button>
              <Button variant="outline" size="sm">
                <Trash2 className="h-4 w-4 mr-2" />
                Remove<span className="placeholder-indicator">⭐</span>
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Library Items */}
      <div className="flex-1 min-h-0">
        <ScrollArea className="h-full max-h-[calc(100vh-20rem)]">
          <div className="p-6 space-y-4">
            {filteredItems.map((item) => (
              <Card 
                key={item.id} 
                className={`lgcustom-hover-transform cursor-pointer transition-all ${
                  selectedItems.includes(item.id) ? 'ring-2 ring-primary' : ''
                }`}
                onClick={() => toggleSelection(item.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <Badge variant="default" className="bg-primary">
                          Signal
                        </Badge>
                        <Badge variant={item.priority === 'High' ? 'destructive' : 'secondary'}>
                          {item.priority} Priority
                        </Badge>
                        <Badge variant="outline">
                          {item.category}
                        </Badge>
                      </div>
                      <CardTitle className="text-lg line-clamp-2 mb-2">{item.title}</CardTitle>
                      <CardDescription className="text-sm">{item.source}</CardDescription>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <div className="text-right">
                        <div className="text-sm font-medium">{(item.confidence * 100).toFixed(0)}%</div>
                        <div className="text-xs text-muted-foreground">Confidence</div>
                      </div>
                      <Button variant="ghost" size="sm">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                    {item.summary}
                  </p>
                  
                  <Separator className="my-3" />
                  
                  <div className="flex items-center justify-between">
                    <div className="flex flex-wrap gap-1">
                      {item.tags.slice(0, 4).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          <Tag className="h-3 w-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                      {item.tags.length > 4 && (
                        <Badge variant="outline" className="text-xs">
                          +{item.tags.length - 4} more
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      <span>Added {item.dateAdded}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  )
}

export default Library

