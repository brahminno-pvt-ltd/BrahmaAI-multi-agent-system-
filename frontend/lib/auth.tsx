'use client'

import {
  createContext, useContext, useEffect, useState,
  useCallback, type ReactNode
} from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { authApi } from '@/lib/api'

export type Role = 'admin' | 'user'

export type AuthUser = {
  username: string
  role: Role
  token: string
}

type AuthCtx = {
  user: AuthUser | null
  isAdmin: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthCtx>({
  user: null,
  isAdmin: false,
  isLoading: true,
  login: async () => {},
  logout: () => {},
})

// Pages that don't require authentication
const PUBLIC_PATHS = ['/login']

// Pages that require admin role
const ADMIN_PATHS = ['/admin']

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  // Restore session from localStorage on mount
  useEffect(() => {
    const restore = async () => {
      const token = localStorage.getItem('brahma_token')
      const username = localStorage.getItem('brahma_username')
      const role = localStorage.getItem('brahma_role') as Role | null

      if (token && username && role) {
        // Verify token is still valid
        try {
          await authApi.me(token)
          setUser({ username, role, token })
        } catch {
          // Token expired — clear storage
          clearStorage()
        }
      }
      setIsLoading(false)
    }
    restore()
  }, [])

  // Route guard
  useEffect(() => {
    if (isLoading) return

    const isPublic = PUBLIC_PATHS.some(p => pathname.startsWith(p))
    const isAdminPath = ADMIN_PATHS.some(p => pathname.startsWith(p))

    if (!user && !isPublic) {
      router.replace('/login')
      return
    }

    if (isAdminPath && user?.role !== 'admin') {
      router.replace('/chat')
      return
    }

    if (user && isPublic) {
      router.replace('/chat')
    }
  }, [user, isLoading, pathname, router])

  const login = useCallback(async (username: string, password: string) => {
    const res = await authApi.login(username, password)

    // Derive role from username — in production this comes from the API response
    const role: Role = username === 'admin' ? 'admin' : 'user'

    const authUser: AuthUser = {
      username: res.username,
      role,
      token: res.access_token,
    }

    localStorage.setItem('brahma_token', res.access_token)
    localStorage.setItem('brahma_username', res.username)
    localStorage.setItem('brahma_role', role)

    setUser(authUser)
    router.replace('/chat')
  }, [router])

  const logout = useCallback(() => {
    clearStorage()
    setUser(null)
    router.replace('/login')
  }, [router])

  const isAdmin = user?.role === 'admin'

  return (
    <AuthContext.Provider value={{ user, isAdmin, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

function clearStorage() {
  localStorage.removeItem('brahma_token')
  localStorage.removeItem('brahma_username')
  localStorage.removeItem('brahma_role')
}

export const useAuth = () => useContext(AuthContext)
