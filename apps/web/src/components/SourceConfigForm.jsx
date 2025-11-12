import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Plus, Trash2, Info } from 'lucide-react'
import InfoTooltip from './InfoTooltip.jsx'

const SourceConfigForm = ({ config, onChange }) => {
  const [localConfig, setLocalConfig] = useState(config || {
    start_urls: [],
    crawl_scope: {
      max_depth: 3,
      max_artifacts: 0
    },
    filtering: {
      allowed_domains: []
    },
    extraction: {
      extract_documents: true,
      extract_pdfs: true,
      max_document_size_mb: 50
    }
  })

  const updateConfig = (updates) => {
    const newConfig = { ...localConfig, ...updates }
    setLocalConfig(newConfig)
    onChange(newConfig)
  }

  const addUrl = () => {
    const newUrls = [...(localConfig.start_urls || []), '']
    updateConfig({ start_urls: newUrls })
  }

  const updateUrl = (index, value) => {
    const newUrls = [...(localConfig.start_urls || [])]
    newUrls[index] = value
    updateConfig({ start_urls: newUrls })
  }

  const removeUrl = (index) => {
    const newUrls = localConfig.start_urls.filter((_, i) => i !== index)
    updateConfig({ start_urls: newUrls })
  }

  const addDomain = () => {
    const newDomains = [...(localConfig.filtering?.allowed_domains || []), '']
    updateConfig({
      filtering: {
        ...localConfig.filtering,
        allowed_domains: newDomains
      }
    })
  }

  const updateDomain = (index, value) => {
    const newDomains = [...(localConfig.filtering?.allowed_domains || [])]
    newDomains[index] = value
    updateConfig({
      filtering: {
        ...localConfig.filtering,
        allowed_domains: newDomains
      }
    })
  }

  const removeDomain = (index) => {
    const newDomains = localConfig.filtering?.allowed_domains.filter((_, i) => i !== index) || []
    updateConfig({
      filtering: {
        ...localConfig.filtering,
        allowed_domains: newDomains
      }
    })
  }

  const updateCrawlScope = (field, value) => {
    updateConfig({
      crawl_scope: {
        ...localConfig.crawl_scope,
        [field]: value
      }
    })
  }

  return (
    <div className="space-y-6">
      {/* Start URLs */}
      <div>
        <div className="flex items-center space-x-2 mb-2">
          <Label>Start URLs *</Label>
          <InfoTooltip content="These are the starting points for the web crawler. The crawler will begin at these URLs and follow links to discover more pages. Think of these as the entry points to a website. You can add multiple URLs if you want to crawl multiple pages or websites. Each URL should be a complete web address starting with http:// or https://." />
        </div>
        <div className="space-y-2">
          {(localConfig.start_urls || []).map((url, index) => (
            <div key={index} className="flex items-center space-x-2">
              <Input
                type="url"
                value={url}
                onChange={(e) => updateUrl(index, e.target.value)}
                placeholder="https://example.com"
                className="flex-1"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => removeUrl(index)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addUrl}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add URL
          </Button>
        </div>
      </div>

      <Separator />

      {/* Crawl Scope */}
      <div>
        <div className="flex items-center space-x-2 mb-4">
          <Label className="text-base font-semibold">Crawl Scope</Label>
          <InfoTooltip content="Crawl scope controls how far and how much the crawler will explore. Think of it like setting boundaries for how deep into a website the crawler should go and how many pages it should collect." />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Label htmlFor="max_depth">Max Depth</Label>
              <InfoTooltip content="This controls how many levels deep the crawler will go from your start URLs. Depth 1 means only the start URLs themselves. Depth 2 means the start URLs plus pages linked directly from them. Depth 3 adds another level, and so on. Higher values will crawl more pages but take significantly longer and use more resources. For most websites, a depth of 2-3 is sufficient to capture the main content without crawling too many navigation or footer pages." />
            </div>
            <Input
              id="max_depth"
              type="number"
              min="1"
              max="10"
              value={localConfig.crawl_scope?.max_depth || 3}
              onChange={(e) => updateCrawlScope('max_depth', parseInt(e.target.value) || 3)}
            />
            <p className="text-xs text-muted-foreground mt-1">
              {localConfig.crawl_scope?.max_depth === 1 && 'Only start URLs'}
              {localConfig.crawl_scope?.max_depth === 2 && 'Start URLs + 1 level deep'}
              {localConfig.crawl_scope?.max_depth === 3 && 'Start URLs + 2 levels deep'}
              {localConfig.crawl_scope?.max_depth > 3 && `${localConfig.crawl_scope?.max_depth - 1} levels deep`}
            </p>
          </div>
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Label htmlFor="max_artifacts">Max Artifacts</Label>
              <InfoTooltip content="This sets a limit on the total number of pages or documents the crawler will collect. Each page that contains content becomes an 'artifact' in the system. Setting this to 0 means unlimited - the crawler will collect as many pages as it finds within the depth limit. Setting a specific number (like 100 or 1000) is useful if you only want a sample of content or want to limit resource usage. Once the limit is reached, crawling stops even if more pages are available." />
            </div>
            <Input
              id="max_artifacts"
              type="number"
              min="0"
              value={localConfig.crawl_scope?.max_artifacts || 0}
              onChange={(e) => updateCrawlScope('max_artifacts', parseInt(e.target.value) || 0)}
            />
            <p className="text-xs text-muted-foreground mt-1">
              {localConfig.crawl_scope?.max_artifacts === 0 ? 'Unlimited - collect all pages found' : `Limited to ${localConfig.crawl_scope?.max_artifacts} pages`}
            </p>
          </div>
        </div>
      </div>

      <Separator />

      {/* Document Extraction */}
      <div>
        <div className="flex items-center space-x-2 mb-4">
          <Label className="text-base font-semibold">Document Extraction</Label>
          <InfoTooltip content="Configure how the crawler handles PDFs and other document files found on websites. You can enable or disable document extraction, choose which types to download, and set size limits." />
        </div>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="extract_documents"
              checked={localConfig.extraction?.extract_documents !== false}
              onChange={(e) => {
                const extraction = {
                  ...localConfig.extraction,
                  extract_documents: e.target.checked,
                  extract_pdfs: e.target.checked ? (localConfig.extraction?.extract_pdfs !== false) : false
                }
                updateConfig({ extraction })
              }}
              className="rounded"
            />
            <Label htmlFor="extract_documents" className="font-normal cursor-pointer">
              Extract Documents
            </Label>
            <InfoTooltip content="When enabled, the crawler will download and process document files (PDFs, Word docs, PowerPoint, Excel, etc.) found on websites. When disabled, only web pages will be crawled." />
          </div>
          
          {localConfig.extraction?.extract_documents !== false && (
            <div className="pl-6 space-y-3">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="extract_pdfs"
                  checked={localConfig.extraction?.extract_pdfs !== false}
                  onChange={(e) => {
                    const extraction = {
                      ...localConfig.extraction,
                      extract_pdfs: e.target.checked
                    }
                    updateConfig({ extraction })
                  }}
                  className="rounded"
                />
                <Label htmlFor="extract_pdfs" className="font-normal cursor-pointer">
                  Extract PDFs Specifically
                </Label>
                <InfoTooltip content="Enable downloading and processing of PDF documents. PDFs are often used for research papers, reports, and official documents. Disable this if you only want web pages." />
              </div>
              
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <Label htmlFor="max_document_size_mb">Maximum Document Size (MB)</Label>
                  <InfoTooltip content="Documents larger than this size will be skipped to prevent downloading very large files that may not be useful. The default is 50MB, which covers most documents. Increase if you need to download large research papers or reports." />
                </div>
                <Input
                  id="max_document_size_mb"
                  type="number"
                  min="1"
                  max="500"
                  value={localConfig.extraction?.max_document_size_mb || 50}
                  onChange={(e) => {
                    const extraction = {
                      ...localConfig.extraction,
                      max_document_size_mb: parseInt(e.target.value) || 50
                    }
                    updateConfig({ extraction })
                  }}
                  className="w-32"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <Separator />

      {/* Filtering */}
      <div>
        <div className="flex items-center space-x-2 mb-2">
          <Label className="text-base font-semibold">Filtering</Label>
          <InfoTooltip content="Filtering helps you control which websites and pages the crawler is allowed to visit. This prevents the crawler from following links to external websites you don't want to include in your collection." />
        </div>
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <Label>Allowed Domains</Label>
            <InfoTooltip content="This restricts crawling to only the domains you specify. For example, if your start URL is 'example.com' and you add 'example.com' to allowed domains, the crawler will only visit pages on example.com and ignore links to other websites. If you leave this empty, the crawler will follow links to any domain found in your start URLs. This is useful when you want to stay within a specific website or set of related sites. Enter domains without 'http://' or 'www' (e.g., 'example.com' or 'subdomain.example.com')." />
          </div>
          <div className="space-y-2">
            {(localConfig.filtering?.allowed_domains || []).map((domain, index) => (
              <div key={index} className="flex items-center space-x-2">
                <Input
                  value={domain}
                  onChange={(e) => updateDomain(index, e.target.value)}
                  placeholder="example.com"
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => removeDomain(index)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addDomain}
              className="w-full"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Domain
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SourceConfigForm

