"use client"

import React, { createContext, useContext, useEffect, useState, useCallback } from "react"
import { useSession, signOut } from "next-auth/react" // <-- Added NextAuth Bridge

interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_verified: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (token: string, userData?: User) => void
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // 1. Listen to Google / NextAuth
  const { data: session, status } = useSession() 
  
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const logout = useCallback(async () => {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    setUser(null)
    setToken(null)
    
    // Log out of Google as well, then redirect
    await signOut({ redirect: false })
    window.location.href = "/"
  }, [])

  const refreshUser = useCallback(async () => { 
    // 1. If Google already authenticated us, DO NOT wipe the state. Just stop here. 
    if (status === "authenticated") { 
      setIsLoading(false); 
      return; 
    } 

    const currentToken = localStorage.getItem("token") 
    if (!currentToken) { 
      setUser(null) 
      setToken(null) 
      setIsLoading(false) 
      return 
    } 

    setToken(currentToken) 
    try { 
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/me`, { 
        headers: { Authorization: `Bearer ${currentToken}` }, 
      }) 

      if (response.ok) { 
        const userData = await response.json() 
        setUser(userData) 
        localStorage.setItem("user", JSON.stringify(userData)) 
      } else { 
        if (response.status === 401) { 
          // Only log out if we are ALSO not authenticated by Google 
          // status !== "authenticated" is guaranteed here because of the early return above.
          logout() 
        } 
      } 
    } catch (error) { 
      console.error("Failed to fetch user profile", error) 
    } finally { 
      setIsLoading(false) 
    } 
  }, [status, logout])

  // 2. THE NEURAL LINK: Synchronize Google Session with Custom State
  useEffect(() => {
    if (status === "loading") {
      setIsLoading(true)
      return
    }

    if (status === "authenticated" && session?.user) {
      // Google logged us in! Inject data so the frontend knows who you are.
      setUser({
        id: session.user.id || "google-sso-user",
        email: session.user.email || "",
        full_name: session.user.name || "Analyst",
        is_active: true,
        is_verified: true,
      })
      
      // Provide a proxy token so the frontend doesn't kick you out during uploads
      const proxyToken = (session as any)?.accessToken || "google-sso-active"
      setToken(proxyToken)
      setIsLoading(false)
    } else if (status === "unauthenticated") {
      // If not logged in with Google, fallback to classic email/password check
      refreshUser()
    }
  }, [session, status, refreshUser])

  const login = (newToken: string, userData?: User) => {
    localStorage.setItem("token", newToken)
    setToken(newToken)
    if (userData) {
      localStorage.setItem("user", JSON.stringify(userData))
      setUser(userData)
    }
    refreshUser()
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}