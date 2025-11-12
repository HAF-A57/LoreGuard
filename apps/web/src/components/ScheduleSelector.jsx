import { useState, useEffect } from 'react'
import { Label } from '@/components/ui/label.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Input } from '@/components/ui/input.jsx'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group.jsx'
import InfoTooltip from './InfoTooltip.jsx'

const presetSchedules = {
    'every-5-min': { cron: '*/5 * * * *', label: 'Every 5 minutes', description: 'Very frequent updates' },
    'every-15-min': { cron: '*/15 * * * *', label: 'Every 15 minutes', description: 'Frequent updates' },
    'every-30-min': { cron: '*/30 * * * *', label: 'Every 30 minutes', description: 'Regular updates' },
    'every-hour': { cron: '0 * * * *', label: 'Every hour', description: 'Hourly updates' },
    'every-2-hours': { cron: '0 */2 * * *', label: 'Every 2 hours', description: 'Bi-hourly updates' },
    'every-4-hours': { cron: '0 */4 * * *', label: 'Every 4 hours', description: 'Quarterly updates' },
    'every-6-hours': { cron: '0 */6 * * *', label: 'Every 6 hours', description: 'Four times daily' },
    'every-12-hours': { cron: '0 */12 * * *', label: 'Every 12 hours', description: 'Twice daily' },
    'daily': { cron: '0 0 * * *', label: 'Daily (midnight)', description: 'Once per day at midnight' },
    'daily-morning': { cron: '0 9 * * *', label: 'Daily (9 AM)', description: 'Once per day at 9 AM' },
    'daily-evening': { cron: '0 18 * * *', label: 'Daily (6 PM)', description: 'Once per day at 6 PM' },
    'weekly': { cron: '0 0 * * 0', label: 'Weekly (Sunday)', description: 'Once per week on Sunday' },
    'monthly': { cron: '0 0 1 * *', label: 'Monthly (1st)', description: 'Once per month on the 1st' }
  }

const ScheduleSelector = ({ value, onChange }) => {
  // Find matching preset or default to custom
  const findPresetForCron = (cron) => {
    if (!cron) return ''
    for (const [key, preset] of Object.entries(presetSchedules)) {
      if (preset.cron === cron) return key
    }
    return ''
  }

  const [scheduleType, setScheduleType] = useState(() => {
    if (!value || value === '') return 'manual'
    // Check if it matches a preset
    const preset = findPresetForCron(value)
    if (preset) return 'preset'
    // Try to detect if it's a cron expression
    if (value.match(/^[\d\s\*\/,-]+$/)) return 'custom'
    return 'manual'
  })

  const [customCron, setCustomCron] = useState(value || '')
  const [presetSchedule, setPresetSchedule] = useState(() => findPresetForCron(value || ''))

  // Update state when value prop changes (e.g., when editing existing source)
  useEffect(() => {
    const currentCron = value || ''
    if (currentCron !== customCron) {
      setCustomCron(currentCron)
      const preset = findPresetForCron(currentCron)
      setPresetSchedule(preset)
      
      if (!currentCron) {
        setScheduleType('manual')
      } else if (preset) {
        setScheduleType('preset')
      } else if (currentCron.match(/^[\d\s\*\/,-]+$/)) {
        setScheduleType('custom')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  const handleScheduleTypeChange = (type) => {
    setScheduleType(type)
    if (type === 'manual') {
      onChange('')
      setCustomCron('')
      setPresetSchedule('')
    } else if (type === 'preset' && presetSchedule) {
      onChange(presetSchedules[presetSchedule].cron)
    }
  }

  const handlePresetChange = (preset) => {
    setPresetSchedule(preset)
    if (preset && presetSchedules[preset]) {
      const cron = presetSchedules[preset].cron
      onChange(cron)
      setCustomCron(cron)
    }
  }

  const handleCustomCronChange = (cron) => {
    setCustomCron(cron)
    onChange(cron)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Label className="text-base font-semibold">Crawl Schedule</Label>
        <InfoTooltip content="Configure when this source should automatically crawl for new content. Choose manual to only crawl when you trigger it manually." />
      </div>

      <RadioGroup value={scheduleType} onValueChange={handleScheduleTypeChange} className="space-y-4">
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="manual" id="manual" />
          <Label htmlFor="manual" className="font-normal cursor-pointer">
            Manual Only
            <span className="text-xs text-muted-foreground ml-2">
              (Crawl only when I trigger it manually)
            </span>
          </Label>
        </div>

        <div className="space-y-3 pl-6">
          <RadioGroupItem value="preset" id="preset" />
          <div className="space-y-2">
            <Label htmlFor="preset" className="font-normal cursor-pointer">
              Use Preset Schedule
            </Label>
            {scheduleType === 'preset' && (
              <Select value={presetSchedule} onValueChange={handlePresetChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a schedule..." />
                </SelectTrigger>
                <SelectContent>
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                    Frequent Updates
                  </div>
                  {Object.entries(presetSchedules).slice(0, 3).map(([key, preset]) => (
                    <SelectItem key={key} value={key}>
                      <div>
                        <div className="font-medium">{preset.label}</div>
                        <div className="text-xs text-muted-foreground">{preset.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground mt-2">
                    Regular Updates
                  </div>
                  {Object.entries(presetSchedules).slice(3, 7).map(([key, preset]) => (
                    <SelectItem key={key} value={key}>
                      <div>
                        <div className="font-medium">{preset.label}</div>
                        <div className="text-xs text-muted-foreground">{preset.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground mt-2">
                    Daily Updates
                  </div>
                  {Object.entries(presetSchedules).slice(7, 10).map(([key, preset]) => (
                    <SelectItem key={key} value={key}>
                      <div>
                        <div className="font-medium">{preset.label}</div>
                        <div className="text-xs text-muted-foreground">{preset.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground mt-2">
                    Less Frequent
                  </div>
                  {Object.entries(presetSchedules).slice(10).map(([key, preset]) => (
                    <SelectItem key={key} value={key}>
                      <div>
                        <div className="font-medium">{preset.label}</div>
                        <div className="text-xs text-muted-foreground">{preset.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        <div className="space-y-3 pl-6">
          <RadioGroupItem value="custom" id="custom" />
          <div className="space-y-2">
            <Label htmlFor="custom" className="font-normal cursor-pointer">
              Custom Cron Expression
              <span className="text-xs text-muted-foreground ml-2">
                (Advanced users only)
              </span>
            </Label>
            {scheduleType === 'custom' && (
              <div className="space-y-2">
                <Input
                  value={customCron}
                  onChange={(e) => handleCustomCronChange(e.target.value)}
                  placeholder="0 * * * *"
                  className="font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground">
                  Format: minute hour day month weekday (e.g., "0 9 * * *" = daily at 9 AM)
                </p>
                <div className="text-xs text-muted-foreground space-y-1 p-2 bg-muted rounded-md">
                  <div><strong>Examples:</strong></div>
                  <div>• <code className="bg-background px-1 rounded">0 * * * *</code> - Every hour</div>
                  <div>• <code className="bg-background px-1 rounded">0 9 * * *</code> - Daily at 9 AM</div>
                  <div>• <code className="bg-background px-1 rounded">0 0 * * 0</code> - Weekly on Sunday</div>
                  <div>• <code className="bg-background px-1 rounded">*/15 * * * *</code> - Every 15 minutes</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </RadioGroup>
    </div>
  )
}

export default ScheduleSelector

