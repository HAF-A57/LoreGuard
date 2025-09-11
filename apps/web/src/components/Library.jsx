import { useState } from 'react'
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
  Plus
} from 'lucide-react'

const Library = () => {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedItems, setSelectedItems] = useState([])

  // Mock data for library items
  const libraryItems = [
    {
      id: 1,
      title: "NATO Strategic Assessment: Eastern European Defense Posture",
      source: "NATO Strategic Communications Centre",
      dateAdded: "2024-09-08",
      confidence: 0.92,
      tags: ["Defense", "NATO", "Eastern Europe", "Strategic"],
      summary: "Comprehensive analysis of NATO's defensive capabilities and strategic positioning in Eastern Europe.",
      category: "Military Strategy",
      priority: "High"
    },
    {
      id: 2,
      title: "Economic Impact of Sanctions on Global Supply Chains",
      source: "International Economic Forum",
      dateAdded: "2024-09-07",
      confidence: 0.87,
      tags: ["Economics", "Supply Chain", "Sanctions", "Global"],
      summary: "Detailed examination of how international sanctions affect global supply chain networks.",
      category: "Economic Analysis",
      priority: "High"
    },
    {
      id: 3,
      title: "Cybersecurity Threats in Critical Infrastructure",
      source: "Cybersecurity Research Institute",
      dateAdded: "2024-09-06",
      confidence: 0.89,
      tags: ["Cybersecurity", "Infrastructure", "Threats", "Critical"],
      summary: "Analysis of emerging cybersecurity threats targeting critical infrastructure systems.",
      category: "Cybersecurity",
      priority: "Medium"
    },
    {
      id: 4,
      title: "Regional Stability Assessment: Middle East",
      source: "International Relations Institute",
      dateAdded: "2024-09-05",
      confidence: 0.84,
      tags: ["Middle East", "Stability", "Regional", "Politics"],
      summary: "Comprehensive assessment of political and military stability in the Middle East region.",
      category: "Regional Analysis",
      priority: "Medium"
    }
  ]

  const filteredItems = libraryItems.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const toggleSelection = (itemId) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">Signal Library</h1>
            <p className="text-muted-foreground">Curated high-value documents for distribution</p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Archive className="h-4 w-4 mr-2" />
              Export Selected
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add to Library
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
            Filters
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
                Share
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button variant="outline" size="sm">
                <Trash2 className="h-4 w-4 mr-2" />
                Remove
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Library Items */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-6 space-y-4">
            {filteredItems.map((item) => (
              <Card 
                key={item.id} 
                className={`aulendur-hover-transform cursor-pointer transition-all ${
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

