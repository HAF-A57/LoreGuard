import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { 
  Eye, 
  EyeOff, 
  Shield, 
  Lock,
  Mail,
  AlertCircle,
  CheckCircle
} from 'lucide-react'

const Login = ({ onLogin }) => {
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Simulate authentication
    setTimeout(() => {
      if (formData.email && formData.password) {
        onLogin && onLogin()
      } else {
        setError('Please enter both email and password')
      }
      setIsLoading(false)
    }, 1500)
  }

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
    setError('')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-aulendur-cream via-aulendur-sage to-aulendur-steel flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-aulendur-navy rounded-xl flex items-center justify-center mx-auto mb-4">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-aulendur-navy mb-2">LoreGuard</h1>
          <p className="text-aulendur-steel">Facts & Perspectives Harvesting System</p>
        </div>

        {/* Login Card */}
        <Card className="aulendur-gradient-card shadow-2xl">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Welcome Back<span className="placeholder-indicator">⭐</span></CardTitle>
            <CardDescription>Sign in to access your LoreGuard dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span className="text-sm text-red-700">{error}</span>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="email"
                    name="email"
                    placeholder="Enter your email"
                    value={formData.email}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleChange}
                    className="pl-10 pr-10"
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center space-x-2">
                  <input type="checkbox" className="rounded" />
                  <span>Remember me<span className="placeholder-indicator">⭐</span></span>
                </label>
                <Button variant="link" className="p-0 h-auto text-primary">
                  Forgot password?<span className="placeholder-indicator">⭐</span>
                </Button>
              </div>

              <Button 
                type="submit" 
                className="w-full aulendur-hover-transform"
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Signing in...</span>
                  </div>
                ) : (
                  <>
                    Sign In<span className="placeholder-indicator">⭐</span>
                  </>
                )}
              </Button>
            </form>

            <Separator className="my-6" />

            <div className="text-center space-y-4">
              <p className="text-sm text-muted-foreground">
                Need access to LoreGuard?
              </p>
              <Button variant="outline" className="w-full">
                Request Access<span className="placeholder-indicator">⭐</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-aulendur-steel">
          <div className="flex items-center justify-center space-x-2 mb-2">
            <CheckCircle className="h-4 w-4" />
            <span>Secure Authentication</span>
          </div>
          <p>© 2024 Air Force Wargaming. All rights reserved.</p>
        </div>
      </div>
    </div>
  )
}

export default Login

