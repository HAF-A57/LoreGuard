import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { 
  LayoutDashboard,
  FileText, 
  Globe, 
  BookOpen,
  Target,
  Settings as SettingsIcon,
  BarChart3,
  Briefcase,
  Moon,
  Sun,
  Menu,
  X,
  MessageSquare
} from 'lucide-react'
import './App.css'

// Import page components
import Dashboard from './components/Dashboard.jsx'
import Artifacts from './components/Artifacts.jsx'
import Sources from './components/Sources.jsx'
import Library from './components/Library.jsx'
import Evaluations from './components/Evaluations.jsx'
import Jobs from './components/Jobs.jsx'
import Analytics from './components/Analytics.jsx'
import Settings from './components/Settings.jsx'
import Login from './components/Login.jsx'
import LoadingScreen from './components/LoadingScreen.jsx'
import NotFound from './components/NotFound.jsx'
import AIAssistant from './components/AIAssistant.jsx'
import { Toaster } from './components/ui/sonner.jsx'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  // Default to dark mode, but check localStorage for saved preference
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('loreguard_theme')
    return savedTheme ? savedTheme === 'dark' : true // Default to dark mode
  })
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [assistantCollapsed, setAssistantCollapsed] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [showNotFound, setShowNotFound] = useState(false)

  // Initialize app and theme
  useEffect(() => {
    // Apply dark mode class on mount
    if (isDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }

    // Check if user is already authenticated (from localStorage, etc.)
    const checkAuth = () => {
      const savedAuth = localStorage.getItem('loreguard_auth')
      if (savedAuth) {
        setIsAuthenticated(true)
      }
      setIsLoading(false)
    }

    // Simulate initial loading
    setTimeout(checkAuth, 3000)
  }, [isDarkMode])

  const toggleTheme = () => {
    const newDarkMode = !isDarkMode
    setIsDarkMode(newDarkMode)
    if (newDarkMode) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('loreguard_theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('loreguard_theme', 'light')
    }
  }

  const handleLogin = () => {
    setIsAuthenticated(true)
    localStorage.setItem('loreguard_auth', 'true')
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    localStorage.removeItem('loreguard_auth')
    setCurrentPage('dashboard')
  }

  const handleNavigateTo = (page) => {
    if (navigation.find(nav => nav.id === page)) {
      setCurrentPage(page)
      setShowNotFound(false)
    } else {
      setShowNotFound(true)
    }
  }

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard, component: Dashboard },
    { id: 'artifacts', name: 'Artifacts', icon: FileText, component: Artifacts },
    { id: 'sources', name: 'Sources', icon: Globe, component: Sources },
    { id: 'library', name: 'Signals Library', icon: BookOpen, component: Library },
    { id: 'evaluations', name: 'Evaluations', icon: Target, component: Evaluations },
    { id: 'jobs', name: 'Jobs', icon: Briefcase, component: Jobs },
    { id: 'analytics', name: 'Analytics', icon: BarChart3, component: Analytics },
    { id: 'settings', name: 'Settings', icon: SettingsIcon, component: Settings }
  ]

  // Show loading screen
  if (isLoading) {
    return <LoadingScreen onLoadingComplete={() => setIsLoading(false)} />
  }

  // Show login screen
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />
  }

  // Show 404 page
  if (showNotFound) {
    return (
      <NotFound 
        onNavigateHome={handleNavigateTo}
        onNavigateBack={() => setShowNotFound(false)}
      />
    )
  }

  const currentNav = navigation.find(nav => nav.id === currentPage)
  const CurrentComponent = currentNav?.component || Dashboard

  return (
    <div className={`min-h-screen bg-background ${isDarkMode ? 'dark' : ''}`}>
      {/* Header */}
      <header className="h-16 bg-gradient-to-r from-aulendur-cream via-aulendur-sage to-aulendur-steel border-b border-border flex items-center justify-between px-6">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="lg:hidden"
          >
            {sidebarCollapsed ? <Menu className="h-4 w-4" /> : <X className="h-4 w-4" />}
          </Button>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-aulendur-navy rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-base">LG</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-aulendur-navy tracking-wide header-title">Global Facts & Perspectives Harvesting</h1>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setAssistantCollapsed(!assistantCollapsed)}
            className="aulendur-hover-transform"
          >
            <MessageSquare className="h-4 w-4" />
            {!assistantCollapsed && <span className="ml-2 hidden md:inline">AI Assistant</span>}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            className="aulendur-hover-transform"
          >
            {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          <div className="text-sm text-aulendur-steel font-medium">
            Air Force Wargaming
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="aulendur-hover-transform"
          >
            Logout
          </Button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
        {/* Left Sidebar */}
        <aside className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-sidebar border-r border-sidebar-border transition-all duration-300 flex flex-col flex-shrink-0 h-full overflow-hidden`}>
          {/* Logo Section */}
          <div className="p-6 border-b border-sidebar-border flex-shrink-0">
            <div className="flex items-center justify-center">
              {!sidebarCollapsed ? (
                <div className="flex flex-col items-center">
                  <img 
                    src="/NameandLogo.png"
                    alt="LoreGuard - Global Facts & Perspectives Harvesting" 
                    className="w-76 h-auto max-w-full sidebar-logo"
                    style={{ filter: 'invert(1)' }}
                  />
                </div>
              ) : (
                <div className="w-10 h-10 bg-aulendur-navy rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">LG</span>
                </div>
              )}
            </div>
          </div>
          
          <nav className="flex-1 p-4 overflow-y-auto">
            <ul className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = currentPage === item.id
                
                return (
                  <li key={item.id}>
                    <Button
                      variant={isActive ? "default" : "ghost"}
                      className={`w-full justify-start aulendur-hover-transform sidebar-nav-button ${
                        sidebarCollapsed ? 'px-2' : 'px-3'
                      } ${isActive ? 'active' : ''}`}
                      onClick={() => setCurrentPage(item.id)}
                    >
                      <Icon className="h-4 w-4" />
                      {!sidebarCollapsed && (
                        <span className="ml-3">{item.name}</span>
                      )}
                    </Button>
                  </li>
                )
              })}
            </ul>
          </nav>
        </aside>

        {/* Main Content - Scrollable */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden h-full">
          <div className="min-h-full">
            <CurrentComponent onNavigateTo={handleNavigateTo} />
          </div>
        </main>

        {/* Right Sidebar - AI Assistant */}
        <AIAssistant 
          isCollapsed={assistantCollapsed}
          onToggleCollapse={() => setAssistantCollapsed(!assistantCollapsed)}
        />
      </div>
      
      {/* Toast Notifications */}
      <Toaster />
    </div>
  )
}

export default App

