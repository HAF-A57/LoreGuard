import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import fs from 'fs'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env files with proper priority
  const env = loadEnv(mode, process.cwd(), '')
  
  // Also try to load from parent .env.detected if it exists
  const envDetectedPath = path.resolve(__dirname, '../../.env.detected')
  if (fs.existsSync(envDetectedPath)) {
    const envDetected = fs.readFileSync(envDetectedPath, 'utf-8')
    const lines = envDetected.split('\n')
    
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
        const [key, ...valueParts] = trimmed.split('=')
        const value = valueParts.join('=')
        
        // Convert LOREGUARD_ prefixed vars to VITE_ prefixed
        if (key === 'LOREGUARD_API_URL' && !env.VITE_API_URL) {
          env.VITE_API_URL = value
        } else if (key === 'LOREGUARD_HOST_IP' && !env.VITE_HOST_IP) {
          env.VITE_HOST_IP = value
        }
      }
    }
  }
  
  // Log what we loaded (for debugging)
  console.log('Vite config loaded:', {
    VITE_API_URL: env.VITE_API_URL,
    VITE_HOST_IP: env.VITE_HOST_IP,
    mode
  })
  
  return {
    plugins: [
      react(),
      tailwindcss()
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    define: {
      // Make environment variables available to the app
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL),
      'import.meta.env.VITE_HOST_IP': JSON.stringify(env.VITE_HOST_IP),
      'import.meta.env.VITE_API_PORT': JSON.stringify(env.VITE_API_PORT || '8000'),
    },
    server: {
      port: 6060,
      host: '0.0.0.0',
      strictPort: false, // Allow fallback ports if 6060 is in use
      hmr: {
        protocol: 'ws',
        host: 'localhost', // HMR should use localhost for websocket connection
        port: 6060
      }
    },
    optimizeDeps: {
      exclude: ['lucide-react'] // Prevent issues with icon library
    },
    clearScreen: false // Keep console history visible
  }
})
