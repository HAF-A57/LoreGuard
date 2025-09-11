import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { 
  Home, 
  ArrowLeft, 
  Search, 
  AlertTriangle,
  FileQuestion,
  Compass
} from 'lucide-react'

const NotFound = ({ onNavigateHome, onNavigateBack }) => {
  const quickLinks = [
    { name: 'Dashboard', icon: Home, action: () => onNavigateHome && onNavigateHome('dashboard') },
    { name: 'Artifacts', icon: FileQuestion, action: () => onNavigateHome && onNavigateHome('artifacts') },
    { name: 'Sources', icon: Compass, action: () => onNavigateHome && onNavigateHome('sources') },
    { name: 'Library', icon: Search, action: () => onNavigateHome && onNavigateHome('library') }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-aulendur-cream via-aulendur-sage to-aulendur-steel flex items-center justify-center p-6">
      <div className="w-full max-w-2xl text-center">
        {/* Error Illustration */}
        <div className="mb-8">
          <div className="w-32 h-32 bg-aulendur-navy/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="h-16 w-16 text-aulendur-navy" />
          </div>
          <div className="text-8xl font-bold text-aulendur-navy/20 mb-4">404</div>
          <h1 className="text-4xl font-bold text-aulendur-navy mb-2">Page Not Found</h1>
          <p className="text-lg text-aulendur-steel mb-8">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card className="aulendur-gradient-card aulendur-hover-transform">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <ArrowLeft className="h-5 w-5" />
                <span>Go Back</span>
              </CardTitle>
              <CardDescription>Return to the previous page</CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => onNavigateBack && onNavigateBack()}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go Back
              </Button>
            </CardContent>
          </Card>

          <Card className="aulendur-gradient-card aulendur-hover-transform">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Home className="h-5 w-5" />
                <span>Home</span>
              </CardTitle>
              <CardDescription>Return to the dashboard</CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                className="w-full"
                onClick={() => onNavigateHome && onNavigateHome('dashboard')}
              >
                <Home className="h-4 w-4 mr-2" />
                Go to Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Quick Links */}
        <Card className="aulendur-gradient-card">
          <CardHeader>
            <CardTitle>Quick Navigation</CardTitle>
            <CardDescription>Jump to commonly used sections</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {quickLinks.map((link, index) => {
                const Icon = link.icon
                return (
                  <Button
                    key={index}
                    variant="ghost"
                    className="flex flex-col items-center space-y-2 h-auto py-4 aulendur-hover-transform"
                    onClick={link.action}
                  >
                    <Icon className="h-6 w-6" />
                    <span className="text-sm">{link.name}</span>
                  </Button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Help Section */}
        <div className="mt-8 text-sm text-aulendur-steel">
          <p className="mb-2">Still need help? Contact support or check our documentation.</p>
          <div className="flex items-center justify-center space-x-4">
            <Button variant="link" className="p-0 h-auto">
              Contact Support
            </Button>
            <span>•</span>
            <Button variant="link" className="p-0 h-auto">
              Documentation
            </Button>
            <span>•</span>
            <Button variant="link" className="p-0 h-auto">
              System Status
            </Button>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="w-8 h-8 bg-aulendur-navy rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">LG</span>
            </div>
            <div>
              <div className="text-lg font-bold text-aulendur-navy">LoreGuard</div>
              <div className="text-xs text-aulendur-steel">Facts & Perspectives Harvesting</div>
            </div>
          </div>
          <p className="text-xs text-aulendur-steel">© 2024 Air Force Wargaming. All rights reserved.</p>
        </div>
      </div>
    </div>
  )
}

export default NotFound

