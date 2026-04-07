"use client"

import React, { createContext, useContext, useEffect, useState, useCallback } from "react"

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
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
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
        headers: {
          Authorization: `Bearer ${currentToken}`,
        },
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        localStorage.setItem("user", JSON.stringify(userData))
      } else {
        // Token might be invalid or expired
        if (response.status === 401) {
          logout()
        }
      }
    } catch (error) {
      console.error("Failed to fetch user profile", error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = (newToken: string, userData?: User) => {
    localStorage.setItem("token", newToken)
    setToken(newToken)
    if (userData) {
      localStorage.setItem("user", JSON.stringify(userData))
      setUser(userData)
    }
    refreshUser()
  }

  const logout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    setUser(null)
    setToken(null)
    window.location.href = "/"
  }

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

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
