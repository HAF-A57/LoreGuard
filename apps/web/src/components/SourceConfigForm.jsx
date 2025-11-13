import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Switch } from '@/components/ui/switch.jsx'
import { Plus, Trash2, Info, AlertTriangle, Shield, ShieldAlert } from 'lucide-react'
import InfoTooltip from './InfoTooltip.jsx'

const defaultConfig = {
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
  },
  compliance: {
    obey_robots_txt: true,
    robots_txt_user_agent: '*',
    robots_txt_warning_only: false,
    detect_blockers: true,
    notify_on_blocker: true,
    blocker_response_strategy: 'notify',
    handle_403: 'retry',
    handle_429: 'retry',
    handle_cloudflare: 'notify',
    handle_captcha: 'pause',
    allow_proxy_bypass: false,
    allow_browser_bypass: false,
    allow_user_agent_rotation: true
  }
}

const SourceConfigForm = ({ config, onChange }) => {
  // Merge provided config with defaults
  const mergeConfig = (providedConfig) => {
    if (!providedConfig) return defaultConfig
    
    return {
      ...defaultConfig,
      ...providedConfig,
      crawl_scope: { ...defaultConfig.crawl_scope, ...(providedConfig.crawl_scope || {}) },
      filtering: { ...defaultConfig.filtering, ...(providedConfig.filtering || {}) },
      extraction: { ...defaultConfig.extraction, ...(providedConfig.extraction || {}) },
      compliance: { ...defaultConfig.compliance, ...(providedConfig.compliance || {}) }
    }
  }
  
  const [localConfig, setLocalConfig] = useState(mergeConfig(config))
  
  // Update local config when prop changes
  useEffect(() => {
    setLocalConfig(mergeConfig(config))
  }, [config])

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

  const updateCompliance = (field, value) => {
    updateConfig({
      compliance: {
        ...localConfig.compliance,
        [field]: value
      }
    })
  }

  // Check if risky settings are enabled
  const hasRiskySettings = () => {
    const comp = localConfig.compliance || {}
    return !comp.obey_robots_txt || comp.allow_proxy_bypass || comp.allow_browser_bypass
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

      <Separator />

      {/* Compliance & Blocker Handling */}
      <div>
        <div className="flex items-center space-x-2 mb-4">
          <Label className="text-base font-semibold">Compliance & Blocker Handling</Label>
          <InfoTooltip content="Configure how the crawler handles robots.txt compliance and web crawler blockers. These settings control ethical scraping behavior and how the system responds to anti-bot protections." />
          {hasRiskySettings() && (
            <AlertTriangle className="h-4 w-4 text-orange-500" title="Risky settings enabled - may violate Terms of Service" />
          )}
        </div>

        <div className="space-y-6">
          {/* Robots.txt Compliance */}
          <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-primary" />
              <Label className="text-sm font-semibold">Robots.txt Compliance</Label>
            </div>
            
            <div className="space-y-3 pl-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 flex-1">
                  <Label htmlFor="obey_robots_txt" className="font-normal cursor-pointer">
                    Honor robots.txt
                  </Label>
                  <InfoTooltip content="When enabled, the crawler will respect robots.txt directives from websites. This is the ethical default and recommended for most use cases. Disabling this may violate Terms of Service." />
                </div>
                <Switch
                  id="obey_robots_txt"
                  checked={localConfig.compliance?.obey_robots_txt !== false}
                  onCheckedChange={(checked) => updateCompliance('obey_robots_txt', checked)}
                />
              </div>

              {localConfig.compliance?.obey_robots_txt === false && (
                <div className="flex items-start space-x-2 p-2 bg-orange-500/10 border border-orange-500/30 rounded text-sm">
                  <AlertTriangle className="h-4 w-4 text-orange-500 shrink-0 mt-0.5" />
                  <span className="text-orange-700 dark:text-orange-400">
                    Warning: Ignoring robots.txt may violate Terms of Service and could result in legal issues.
                  </span>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Label htmlFor="robots_txt_user_agent" className="text-sm font-normal">
                  Robots.txt User-Agent:
                </Label>
                <Input
                  id="robots_txt_user_agent"
                  value={localConfig.compliance?.robots_txt_user_agent || '*'}
                  onChange={(e) => updateCompliance('robots_txt_user_agent', e.target.value)}
                  placeholder="*"
                  className="w-32"
                />
                <InfoTooltip content="User-Agent string to use when checking robots.txt. Use '*' for all bots or specify a custom User-Agent." />
              </div>
            </div>
          </div>

          {/* Blocker Detection */}
          <div className="space-y-4 p-4 border rounded-lg">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="h-4 w-4 text-primary" />
              <Label className="text-sm font-semibold">Blocker Detection & Response</Label>
            </div>

            <div className="space-y-4 pl-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 flex-1">
                  <Label htmlFor="detect_blockers" className="font-normal cursor-pointer">
                    Detect Blockers Automatically
                  </Label>
                  <InfoTooltip content="Automatically detect common web crawler blockers like Cloudflare challenges, CAPTCHA pages, and rate limiting. When enabled, the system will identify and respond to these blockers based on your configured strategies." />
                </div>
                <Switch
                  id="detect_blockers"
                  checked={localConfig.compliance?.detect_blockers !== false}
                  onCheckedChange={(checked) => updateCompliance('detect_blockers', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 flex-1">
                  <Label htmlFor="notify_on_blocker" className="font-normal cursor-pointer">
                    Notify on Blocker Detection
                  </Label>
                  <InfoTooltip content="Send notifications when blockers are detected. This helps you stay informed about crawling issues and take appropriate action." />
                </div>
                <Switch
                  id="notify_on_blocker"
                  checked={localConfig.compliance?.notify_on_blocker !== false}
                  onCheckedChange={(checked) => updateCompliance('notify_on_blocker', checked)}
                  disabled={localConfig.compliance?.detect_blockers === false}
                />
              </div>

              {/* Default Blocker Response Strategy */}
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <Label htmlFor="blocker_response_strategy" className="text-sm font-normal">
                    Default Blocker Response:
                  </Label>
                  <InfoTooltip content="Default action when a blocker is detected: abort (stop crawl), retry (retry with different approach), bypass (attempt to bypass), notify (notify and wait for decision)" />
                </div>
                <Select
                  value={localConfig.compliance?.blocker_response_strategy || 'notify'}
                  onValueChange={(value) => updateCompliance('blocker_response_strategy', value)}
                  disabled={localConfig.compliance?.detect_blockers === false}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="abort">Abort - Stop crawl immediately</SelectItem>
                    <SelectItem value="retry">Retry - Retry with different approach</SelectItem>
                    <SelectItem value="bypass">Bypass - Attempt to bypass blocker</SelectItem>
                    <SelectItem value="notify">Notify - Notify and wait for decision</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Per-Blocker-Type Handling */}
              <div className="space-y-3 pt-2">
                <Label className="text-xs font-semibold text-muted-foreground uppercase">Per-Blocker-Type Handling</Label>
                
                <div>
                  <Label htmlFor="handle_403" className="text-xs mb-1 block">403 Forbidden:</Label>
                  <Select
                    value={localConfig.compliance?.handle_403 || 'retry'}
                    onValueChange={(value) => updateCompliance('handle_403', value)}
                    disabled={localConfig.compliance?.detect_blockers === false}
                  >
                    <SelectTrigger className="w-full h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="abort">Abort</SelectItem>
                      <SelectItem value="retry">Retry</SelectItem>
                      <SelectItem value="bypass">Bypass</SelectItem>
                      <SelectItem value="notify">Notify</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="handle_429" className="text-xs mb-1 block">429 Rate Limited:</Label>
                  <Select
                    value={localConfig.compliance?.handle_429 || 'retry'}
                    onValueChange={(value) => updateCompliance('handle_429', value)}
                    disabled={localConfig.compliance?.detect_blockers === false}
                  >
                    <SelectTrigger className="w-full h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="abort">Abort</SelectItem>
                      <SelectItem value="retry">Retry</SelectItem>
                      <SelectItem value="bypass">Bypass</SelectItem>
                      <SelectItem value="notify">Notify</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="handle_cloudflare" className="text-xs mb-1 block">Cloudflare Challenge:</Label>
                  <Select
                    value={localConfig.compliance?.handle_cloudflare || 'notify'}
                    onValueChange={(value) => updateCompliance('handle_cloudflare', value)}
                    disabled={localConfig.compliance?.detect_blockers === false}
                  >
                    <SelectTrigger className="w-full h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="abort">Abort</SelectItem>
                      <SelectItem value="bypass">Bypass</SelectItem>
                      <SelectItem value="notify">Notify</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="handle_captcha" className="text-xs mb-1 block">CAPTCHA Challenge:</Label>
                  <Select
                    value={localConfig.compliance?.handle_captcha || 'pause'}
                    onValueChange={(value) => updateCompliance('handle_captcha', value)}
                    disabled={localConfig.compliance?.detect_blockers === false}
                  >
                    <SelectTrigger className="w-full h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="abort">Abort</SelectItem>
                      <SelectItem value="notify">Notify</SelectItem>
                      <SelectItem value="pause">Pause for Manual Review</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </div>

          {/* Bypass Options */}
          <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="h-4 w-4 text-orange-500" />
              <Label className="text-sm font-semibold">Bypass Options</Label>
              <InfoTooltip content="Advanced options for bypassing blockers. These may violate Terms of Service - use with caution and only when authorized." />
            </div>

            <div className="space-y-3 pl-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 flex-1">
                  <Label htmlFor="allow_user_agent_rotation" className="font-normal cursor-pointer">
                    Allow User-Agent Rotation
                  </Label>
                  <InfoTooltip content="Rotate User-Agent strings to avoid detection. This is generally safe and recommended." />
                </div>
                <Switch
                  id="allow_user_agent_rotation"
                  checked={localConfig.compliance?.allow_user_agent_rotation !== false}
                  onCheckedChange={(checked) => updateCompliance('allow_user_agent_rotation', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 flex-1">
                  <Label htmlFor="allow_proxy_bypass" className="font-normal cursor-pointer">
                    Allow Proxy Bypass
                  </Label>
                  <InfoTooltip content="Use proxy rotation to bypass IP-based blocks. May violate Terms of Service." />
                </div>
                <Switch
                  id="allow_proxy_bypass"
                  checked={localConfig.compliance?.allow_proxy_bypass === true}
                  onCheckedChange={(checked) => updateCompliance('allow_proxy_bypass', checked)}
                />
              </div>

              {localConfig.compliance?.allow_proxy_bypass && (
                <div className="flex items-start space-x-2 p-2 bg-orange-500/10 border border-orange-500/30 rounded text-sm">
                  <AlertTriangle className="h-4 w-4 text-orange-500 shrink-0 mt-0.5" />
                  <span className="text-orange-700 dark:text-orange-400">
                    Warning: Proxy bypass may violate Terms of Service. Use only when authorized.
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 flex-1">
                  <Label htmlFor="allow_browser_bypass" className="font-normal cursor-pointer">
                    Allow Browser Bypass
                  </Label>
                  <InfoTooltip content="Use headless browser (Playwright) to bypass JavaScript challenges. May violate Terms of Service." />
                </div>
                <Switch
                  id="allow_browser_bypass"
                  checked={localConfig.compliance?.allow_browser_bypass === true}
                  onCheckedChange={(checked) => updateCompliance('allow_browser_bypass', checked)}
                />
              </div>

              {localConfig.compliance?.allow_browser_bypass && (
                <div className="flex items-start space-x-2 p-2 bg-orange-500/10 border border-orange-500/30 rounded text-sm">
                  <AlertTriangle className="h-4 w-4 text-orange-500 shrink-0 mt-0.5" />
                  <span className="text-orange-700 dark:text-orange-400">
                    Warning: Browser bypass may violate Terms of Service. Use only when authorized.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SourceConfigForm

