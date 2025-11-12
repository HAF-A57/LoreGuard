import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { 
  FileText, 
  User, 
  Building2, 
  Calendar, 
  Tag, 
  Globe, 
  Languages,
  Link as LinkIcon,
  Hash
} from 'lucide-react'

const ArtifactMetadata = ({ artifact, metadata, clarification }) => {
  if (!artifact && !metadata) {
    return null
  }

  return (
    <div className="space-y-4">
      {/* Basic Artifact Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Artifact Information</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {artifact?.uri && (
              <div className="flex items-start space-x-3">
                <LinkIcon className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-muted-foreground">URI</div>
                  <a 
                    href={artifact.uri} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline break-all"
                  >
                    {artifact.uri}
                  </a>
                </div>
              </div>
            )}
            
            {artifact?.content_hash && (
              <div className="flex items-start space-x-3">
                <Hash className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-muted-foreground">Content Hash</div>
                  <div className="text-sm font-mono break-all">{artifact.content_hash}</div>
                </div>
              </div>
            )}
            
            {artifact?.mime_type && (
              <div className="flex items-center space-x-3">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">MIME Type</div>
                  <div className="text-sm">{artifact.mime_type}</div>
                </div>
              </div>
            )}
            
            {artifact?.version && (
              <div className="flex items-center space-x-3">
                <div className="text-sm font-medium text-muted-foreground">Version</div>
                <Badge variant="outline">{artifact.version}</Badge>
              </div>
            )}
            
            {artifact?.created_at && (
              <div className="flex items-center space-x-3">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Created</div>
                  <div className="text-sm">{new Date(artifact.created_at).toLocaleString()}</div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Document Metadata */}
      {metadata && (
        <Card>
          <CardHeader>
            <CardTitle>Document Metadata</CardTitle>
            <CardDescription>Extracted metadata from the document</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {metadata.title && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">Title</div>
                  <div className="text-base font-semibold">{metadata.title}</div>
                </div>
              )}
              
              {metadata.authors && metadata.authors.length > 0 && (
                <div className="flex items-start space-x-3">
                  <User className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-muted-foreground mb-1">Authors</div>
                    <div className="flex flex-wrap gap-2">
                      {metadata.authors.map((author, idx) => (
                        <Badge key={idx} variant="secondary">{author}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              
              {metadata.organization && (
                <div className="flex items-start space-x-3">
                  <Building2 className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-muted-foreground mb-1">Organization</div>
                    <div className="text-sm">{metadata.organization}</div>
                  </div>
                </div>
              )}
              
              {metadata.pub_date && (
                <div className="flex items-start space-x-3">
                  <Calendar className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-muted-foreground mb-1">Publication Date</div>
                    <div className="text-sm">{new Date(metadata.pub_date).toLocaleDateString()}</div>
                  </div>
                </div>
              )}
              
              {metadata.topics && metadata.topics.length > 0 && (
                <div className="flex items-start space-x-3">
                  <Tag className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-muted-foreground mb-2">Topics</div>
                    <div className="flex flex-wrap gap-2">
                      {metadata.topics.map((topic, idx) => (
                        <Badge key={idx} variant="outline">{topic}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              
              {metadata.geo_location && (
                <div className="flex items-start space-x-3">
                  <Globe className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-muted-foreground mb-1">Geographic Location</div>
                    <div className="text-sm">{metadata.geo_location}</div>
                  </div>
                </div>
              )}
              
              {metadata.language && (
                <div className="flex items-start space-x-3">
                  <Languages className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-muted-foreground mb-1">Language</div>
                    <div className="text-sm">{metadata.language}</div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Clarification Signals */}
      {clarification && clarification.signals && Object.keys(clarification.signals).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Clarification Signals</CardTitle>
            <CardDescription>Signals and evidence for artifact credibility</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(clarification.signals).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between py-2">
                  <span className="text-sm font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                  <Badge variant={value ? 'default' : 'outline'}>
                    {value ? 'Yes' : 'No'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ArtifactMetadata

