import { useState } from 'react'
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
  Eye
} from 'lucide-react'

const Artifacts = () => {
  const [selectedArtifact, setSelectedArtifact] = useState(null)
  const [searchQuery, setSearchQuery] = useState("")

  // Mock data for demonstration
  const mockArtifacts = [
    {
      id: 1,
      title: "NATO Strategic Assessment: Eastern European Defense Posture",
      source: "NATO Strategic Communications Centre",
      date: "2024-09-08",
      confidence: 0.92,
      label: "Signal",
      topics: ["Defense", "NATO", "Eastern Europe"],
      summary: "Comprehensive analysis of NATO's defensive capabilities and strategic positioning in Eastern Europe, including assessment of force readiness and logistical considerations."
    },
    {
      id: 2,
      title: "Economic Impact of Sanctions on Global Supply Chains",
      source: "International Economic Forum",
      date: "2024-09-07",
      confidence: 0.87,
      label: "Signal",
      topics: ["Economics", "Supply Chain", "Sanctions"],
      summary: "Detailed examination of how international sanctions affect global supply chain networks and economic stability across different regions."
    },
    {
      id: 3,
      title: "Cybersecurity Threats in Critical Infrastructure",
      source: "Cybersecurity Research Institute",
      date: "2024-09-06",
      confidence: 0.78,
      label: "Review",
      topics: ["Cybersecurity", "Infrastructure", "Threats"],
      summary: "Analysis of emerging cybersecurity threats targeting critical infrastructure systems and recommended defensive measures."
    }
  ]

  const filteredArtifacts = mockArtifacts.filter(artifact =>
    artifact.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    artifact.topics.some(topic => topic.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="h-full flex">
      {/* Sidebar */}
      <aside className="w-80 bg-sidebar border-r border-sidebar-border flex flex-col">
        <div className="p-4 border-b border-sidebar-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search artifacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4 space-y-3">
            {filteredArtifacts.map((artifact) => (
              <Card
                key={artifact.id}
                className={`cursor-pointer aulendur-hover-transform transition-all ${
                  selectedArtifact?.id === artifact.id ? 'ring-2 ring-primary' : ''
                }`}
                onClick={() => setSelectedArtifact(artifact)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <Badge variant={artifact.label === 'Signal' ? 'default' : 'secondary'}>
                      {artifact.label}
                    </Badge>
                    <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{artifact.date}</span>
                    </div>
                  </div>
                  <CardTitle className="text-sm line-clamp-2">{artifact.title}</CardTitle>
                  <CardDescription className="text-xs">{artifact.source}</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-muted-foreground">Confidence</span>
                    <span className="text-xs font-medium">{(artifact.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={artifact.confidence * 100} className="h-1 mb-2" />
                  <div className="flex flex-wrap gap-1">
                    {artifact.topics.slice(0, 2).map((topic) => (
                      <Badge key={topic} variant="outline" className="text-xs">
                        {topic}
                      </Badge>
                    ))}
                    {artifact.topics.length > 2 && (
                      <Badge variant="outline" className="text-xs">
                        +{artifact.topics.length - 2}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
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

