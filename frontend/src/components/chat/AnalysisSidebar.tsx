"use client"

import React, { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Plus, History, FileText, ChevronLeft, ChevronRight, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/context/AuthContext"

interface Session {
  id: string
  filename: string
  created_at: string
}

export function AnalysisSidebar({ isOpen, toggle }: { isOpen: boolean; toggle: () => void }) {
  const router = useRouter()
  const params = useParams()
  const { user, token, logout } = useAuth()
  const currentId = params?.id as string
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isMounted, setIsMounted] = useState(false)
  const [showLogoutModal, setShowLogoutModal] = useState(false)

  useEffect(() => {
    setIsMounted(true)
    let isSubscribed = true

    const fetchSessions = async () => {
      try {
        const headers: Record<string, string> = {}
        if (token) {
          headers["Authorization"] = `Bearer ${token}`
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/sessions`, {
          headers,
        })
        if (response.ok && isSubscribed) {
          const data = await response.json()
          setSessions(data.sessions || data.items || [])
        } else if (response.status === 401 && isSubscribed) {
          logout()
        }
      } catch (error) {
        if (isSubscribed) console.error("Failed to fetch sessions", error)
      } finally {
        if (isSubscribed) setIsLoading(false)
      }
    }

    if (isMounted) {
      fetchSessions()
    }

    return () => {
      isSubscribed = false
    }
  }, [isMounted, token])

  const handleLogout = () => {
    logout()
  }

  if (!isMounted) return null

  return (
    <>
      {/* Mobile Toggle Button */}
      {!isOpen && (
        <button
          onClick={toggle}
          className="fixed left-4 top-4 z-[60] p-2 bg-charcoal text-white rounded-xl shadow-lg lg:hidden"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      )}

      <motion.aside
        initial={false}
        animate={{ width: isOpen ? 300 : 0, opacity: isOpen ? 1 : 0 }}
        className={cn(
          "fixed inset-y-0 left-0 z-50 bg-charcoal text-cream overflow-hidden border-r border-soft-black flex flex-col",
          !isOpen && "pointer-events-none"
        )}
      >
        {/* Sidebar Header */}
        <div className="p-6 border-b border-soft-black flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-terra flex items-center justify-center">
              <History className="w-4 h-4 text-white" />
            </div>
            <span className="font-display italic font-semibold text-lg">History</span>
          </div>
          <button onClick={toggle} className="p-1 hover:bg-soft-black rounded-md transition-colors">
            <ChevronLeft className="w-5 h-5 text-warm-gray" />
          </button>
        </div>

        {/* New Analysis Button */}
        <div className="p-4">
          <button
            onClick={() => router.push("/analysis")}
            className="w-full py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl flex items-center justify-center gap-2 transition-all font-medium border border-white/5"
          >
            <Plus className="w-4 h-4" />
            New Analysis
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-32 text-warm-gray animate-pulse">
              <div className="text-xs uppercase tracking-widest">Loading history...</div>
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-warm-gray text-sm italic">
              No past sessions found.
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => router.push(`/analysis/${session.id}`)}
                className={cn(
                  "w-full p-3 rounded-xl flex flex-col items-start gap-1 transition-all group",
                  currentId === session.id 
                    ? "bg-accent-terra/20 border border-accent-terra/30 text-white" 
                    : "hover:bg-soft-black text-warm-gray hover:text-cream border border-transparent"
                )}
              >
                <div className="flex items-center gap-2 w-full">
                  <FileText className={cn(
                    "w-4 h-4 flex-shrink-0",
                    currentId === session.id ? "text-accent-terra" : "text-warm-gray group-hover:text-cream"
                  )} />
                  <span className="text-sm font-medium truncate text-left">
                    {session.filename}
                  </span>
                </div>
                <span className="text-[10px] uppercase tracking-tighter opacity-50 ml-6">
                  {new Date(session.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </button>
            ))
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-soft-black">
          <div className="flex items-center justify-between gap-3 px-2">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-accent-gold flex items-center justify-center text-charcoal font-bold text-xs">
                {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase() || "DU"}
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-white truncate max-w-[120px]">{user?.full_name || "Demo User"}</span>
                <span className="text-[10px] text-warm-gray truncate max-w-[120px]">{user?.email || "Free Tier"}</span>
              </div>
            </div>
            <button
              onClick={() => setShowLogoutModal(true)}
              className="p-2 text-warm-gray hover:text-white hover:bg-white/10 rounded-lg transition-all"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.aside>

      {/* Logout Confirmation Modal */}
      <AnimatePresence>
        {showLogoutModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowLogoutModal(false)}
              className="absolute inset-0 bg-charcoal/40 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-sm bg-white rounded-3xl shadow-elegant p-8 text-center"
            >
              <div className="w-16 h-16 bg-beige/50 rounded-full flex items-center justify-center mx-auto mb-6">
                <LogOut className="w-8 h-8 text-charcoal" />
              </div>
              <h3 className="text-xl font-semibold text-charcoal mb-2">Sign Out</h3>
              <p className="text-warm-gray mb-8">Are you sure you want to sign out? Your current session analysis will be saved.</p>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setShowLogoutModal(false)}
                  className="px-6 py-3 rounded-full border border-beige text-charcoal font-medium hover:bg-beige/20 transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleLogout}
                  className="px-6 py-3 rounded-full bg-charcoal text-white font-medium hover:bg-soft-black transition-all shadow-lg hover:shadow-xl"
                >
                  Sign Out
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  )
}
