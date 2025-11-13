import { useState, useEffect } from 'react'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Shield, 
  Database, 
  Brain, 
  Globe, 
  CheckCircle,
  Loader2
} from 'lucide-react'

const LoadingScreen = ({ onLoadingComplete }) => {
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState(0)

  const loadingSteps = [
    { id: 0, name: 'Initializing System', icon: Shield, duration: 800 },
    { id: 1, name: 'Connecting to Database', icon: Database, duration: 1200 },
    { id: 2, name: 'Loading AI Models', icon: Brain, duration: 1500 },
    { id: 3, name: 'Syncing Sources', icon: Globe, duration: 1000 },
    { id: 4, name: 'Ready', icon: CheckCircle, duration: 500 }
  ]

  useEffect(() => {
    let interval
    let stepTimeout

    const startLoading = () => {
      // Progress animation
      interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval)
            setTimeout(() => {
              onLoadingComplete && onLoadingComplete()
            }, 500)
            return 100
          }
          return prev + 1
        })
      }, 50)

      // Step progression
      let totalTime = 0
      loadingSteps.forEach((step, index) => {
        totalTime += step.duration
        setTimeout(() => {
          setCurrentStep(index)
        }, totalTime - step.duration)
      })
    }

    startLoading()

    return () => {
      if (interval) clearInterval(interval)
      if (stepTimeout) clearTimeout(stepTimeout)
    }
  }, [onLoadingComplete])

  const currentStepData = loadingSteps[currentStep]
  const CurrentIcon = currentStepData?.icon || Shield

  return (
    <div className="min-h-screen bg-gradient-to-br from-lgcustom-cream via-lgcustom-sage to-lgcustom-steel dark:from-lgcustom-midnight dark:via-lgcustom-navy dark:to-lgcustom-steel flex items-center justify-center p-6">
      <div className="w-full max-w-md text-center">
        {/* Logo Animation */}
        <div className="mb-8">
          <div className="w-24 h-24 bg-lgcustom-navy dark:bg-lgcustom-steel rounded-2xl flex items-center justify-center mx-auto mb-6 lgcustom-hover-transform animate-pulse shadow-lg">
            <Shield className="h-12 w-12 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-lgcustom-navy dark:text-white mb-2 drop-shadow-sm">LoreGuard</h1>
          <p className="text-lgcustom-steel dark:text-sidebar-foreground/90 font-medium">Facts & Perspectives Harvesting System</p>
        </div>

        {/* Loading Progress */}
        <div className="bg-white/90 dark:bg-card/95 backdrop-blur-sm rounded-2xl p-8 shadow-2xl border border-white/20 dark:border-sidebar-border/50">
          {/* Current Step */}
          <div className="mb-6">
            <div className="w-16 h-16 bg-primary/10 dark:bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-primary/20 dark:border-primary/30">
              {progress === 100 ? (
                <CheckCircle className="h-8 w-8 text-green-500 dark:text-green-400" />
              ) : (
                <CurrentIcon className="h-8 w-8 text-primary dark:text-sidebar-primary animate-pulse" />
              )}
            </div>
            <h3 className="text-lg font-semibold text-foreground dark:text-card-foreground mb-2">
              {currentStepData?.name || 'Loading...'}
            </h3>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between text-sm text-muted-foreground dark:text-sidebar-foreground/80 mb-2 font-medium">
              <span>Loading System</span>
              <span className="font-semibold">{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Loading Steps */}
          <div className="space-y-3">
            {loadingSteps.map((step, index) => {
              const StepIcon = step.icon
              const isActive = index === currentStep
              const isComplete = index < currentStep || progress === 100
              
              return (
                <div 
                  key={step.id}
                  className={`flex items-center space-x-3 p-2 rounded-lg transition-all ${
                    isActive ? 'bg-primary/10 dark:bg-primary/20 border border-primary/20 dark:border-primary/30' : ''
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                    isComplete 
                      ? 'bg-green-500 dark:bg-green-600' 
                      : isActive 
                        ? 'bg-primary dark:bg-sidebar-primary' 
                        : 'bg-muted dark:bg-sidebar-accent/50'
                  }`}>
                    {isComplete ? (
                      <CheckCircle className="h-4 w-4 text-white" />
                    ) : isActive ? (
                      <Loader2 className="h-4 w-4 text-white animate-spin" />
                    ) : (
                      <StepIcon className={`h-4 w-4 ${
                        isComplete 
                          ? 'text-white' 
                          : 'text-muted-foreground dark:text-sidebar-foreground/60'
                      }`} />
                    )}
                  </div>
                  <span className={`text-sm ${
                    isActive 
                      ? 'font-medium text-foreground dark:text-card-foreground' 
                      : 'text-muted-foreground dark:text-sidebar-foreground/70'
                  }`}>
                    {step.name}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-lgcustom-steel dark:text-sidebar-foreground/90">
          <p className="mb-2 font-medium">Built by Air Force Wargaming</p>
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-500/50"></div>
            <span className="font-medium">System Status: Healthy</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoadingScreen

