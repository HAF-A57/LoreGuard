/**
 * LoreGuard Frontend Configuration
 * Uses environment variables with smart fallbacks
 */

// Get API URL from environment or detect from browser location
const getAPIURL = () => {
  // 1. HIGHEST PRIORITY: Explicit VITE_API_URL from environment
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // 2. MEDIUM PRIORITY: Build from VITE_HOST_IP + VITE_API_PORT
  if (import.meta.env.VITE_HOST_IP) {
    const host = import.meta.env.VITE_HOST_IP
    const port = import.meta.env.VITE_API_PORT || '8000'
    const protocol = /^\d+\.\d+\.\d+\.\d+$/.test(host) ? 'http' : 'https'
    return `${protocol}://${host}:${port}`
  }
  
  // 3. FALLBACK: Detect from browser (runtime)
  if (typeof window !== 'undefined') {
    const browserHost = window.location.hostname
    const port = import.meta.env.VITE_API_PORT || '8000'
    
    // If accessing via IP address, use that IP for API too
    if (browserHost !== 'localhost' && browserHost !== '127.0.0.1') {
      const protocol = /^\d+\.\d+\.\d+\.\d+$/.test(browserHost) ? 'http' : 'https'
      return `${protocol}://${browserHost}:${port}`
    }
  }
  
  // 4. DEFAULT: Use localhost (for build time or when all else fails)
  const port = import.meta.env.VITE_API_PORT || '8000'
  return `http://localhost:${port}`
}

// Get host IP
const getHostIP = () => {
  // Use VITE_HOST_IP if available
  if (import.meta.env.VITE_HOST_IP) {
    return import.meta.env.VITE_HOST_IP
  }
  
  // Detect from browser
  if (typeof window !== 'undefined') {
    return window.location.hostname
  }
  
  // Fallback
  return 'localhost'
}

// Get Assistant API URL
const getAssistantURL = () => {
  // Similar logic to API URL but for port 8002
  if (import.meta.env.VITE_ASSISTANT_URL) {
    return import.meta.env.VITE_ASSISTANT_URL
  }
  
  if (import.meta.env.VITE_HOST_IP) {
    const host = import.meta.env.VITE_HOST_IP
    const port = import.meta.env.VITE_ASSISTANT_PORT || '8002'
    const protocol = /^\d+\.\d+\.\d+\.\d+$/.test(host) ? 'http' : 'https'
    return `${protocol}://${host}:${port}`
  }
  
  if (typeof window !== 'undefined') {
    const browserHost = window.location.hostname
    const port = import.meta.env.VITE_ASSISTANT_PORT || '8002'
    
    if (browserHost !== 'localhost' && browserHost !== '127.0.0.1') {
      const protocol = /^\d+\.\d+\.\d+\.\d+$/.test(browserHost) ? 'http' : 'https'
      return `${protocol}://${browserHost}:${port}`
    }
  }
  
  const port = import.meta.env.VITE_ASSISTANT_PORT || '8002'
  return `http://localhost:${port}`
}

export const API_URL = getAPIURL()
export const ASSISTANT_API_URL = getAssistantURL()
export const HOST_IP = getHostIP()

// Log configuration in development
if (import.meta.env.DEV) {
  console.log('LoreGuard Frontend Configuration:', {
    API_URL,
    ASSISTANT_API_URL,
    HOST_IP,
    VITE_API_URL: import.meta.env.VITE_API_URL,
    VITE_HOST_IP: import.meta.env.VITE_HOST_IP,
    VITE_API_PORT: import.meta.env.VITE_API_PORT,
    VITE_ASSISTANT_PORT: import.meta.env.VITE_ASSISTANT_PORT,
    MODE: import.meta.env.MODE
  })
}

