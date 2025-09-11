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
    <div className="min-h-screen bg-gradient-to-br from-aulendur-cream via-aulendur-sage to-aulendur-steel flex items-center justify-center p-6">
      <div className="w-full max-w-md text-center">
        {/* Logo Animation */}
        <div className="mb-8">
          <div className="w-24 h-24 bg-aulendur-navy rounded-2xl flex items-center justify-center mx-auto mb-6 aulendur-hover-transform animate-pulse">
            <Shield className="h-12 w-12 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-aulendur-navy mb-2">LoreGuard</h1>
          <p className="text-aulendur-steel">Facts & Perspectives Harvesting System</p>
        </div>

        {/* Loading Progress */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 shadow-2xl border border-white/20">
          {/* Current Step */}
          <div className="mb-6">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              {progress === 100 ? (
                <CheckCircle className="h-8 w-8 text-green-500" />
              ) : (
                <CurrentIcon className="h-8 w-8 text-primary animate-pulse" />
              )}
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {currentStepData?.name || 'Loading...'}
            </h3>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between text-sm text-muted-foreground mb-2">
              <span>Loading System</span>
              <span>{progress}%</span>
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
                    isActive ? 'bg-primary/10' : ''
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                    isComplete ? 'bg-green-500' : isActive ? 'bg-primary' : 'bg-muted'
                  }`}>
                    {isComplete ? (
                      <CheckCircle className="h-4 w-4 text-white" />
                    ) : isActive ? (
                      <Loader2 className="h-4 w-4 text-white animate-spin" />
                    ) : (
                      <StepIcon className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <span className={`text-sm ${
                    isActive ? 'font-medium text-foreground' : 'text-muted-foreground'
                  }`}>
                    {step.name}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-aulendur-steel">
          <p className="mb-2">Powered by Aulendur LLC</p>
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>System Status: Healthy</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoadingScreen

