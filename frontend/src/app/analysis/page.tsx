"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { 
  Sparkles, 
  ArrowLeft, 
  Upload, 
  History, 
  BarChart3, 
  Clock, 
  ChevronRight, 
  FileText,
  User,
  Plus,
  Loader2,
  Database,
  Shield,
  Zap,
  Brain,
  AlertCircle,
  Download
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import dynamic from "next/dynamic"
import { useAuth } from "@/context/AuthContext"

const ParticleBackground = dynamic(() => import("@/components/ParticleBackground").then(mod => mod.ParticleBackground), { 
  ssr: false 
})

interface RecentAnalysis {
  id: string
  filename: string
  created_at: string
  status: string
}

export default function AnalysisPage() {
  const router = useRouter()
  const { user, token, isLoading: isAuthLoading, logout } = useAuth()
  const [isMounted, setIsMounted] = useState(false)
  const [recentAnalyses, setRecentAnalyses] = useState<RecentAnalysis[]>([])
  const [isLoadingAnalyses, setIsLoadingAnalyses] = useState(true)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setIsMounted(true)
    
    // Fetch Recent Analyses
    const fetchAnalyses = async () => {
      if (!isMounted || isAuthLoading) return
      if (!token) {
        setIsLoadingAnalyses(false)
        return
      }

      try {
        const headers: Record<string, string> = {
          "Authorization": `Bearer ${token}`
        }
        
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/sessions`, {
          headers
        })
        if (res.ok) {
          const data = await res.json()
          setRecentAnalyses(data.sessions || [])
        } else if (res.status === 401) {
          logout()
        }
      } catch (err) {
        console.error("Failed to fetch analyses", err)
      } finally {
        setIsLoadingAnalyses(false)
      }
    }

    fetchAnalyses()
  }, [isMounted, token, isAuthLoading])

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.csv')) return
    
    setIsLoading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analyze-data`, {
        method: "POST",
        body: formData,
        headers: { 
          "Authorization": `Bearer ${token}` 
        }
      })

      if (res.ok) {
        const data = await res.json()
        // Use data.id from the returned AnalysisSession object
        router.push(`/analysis/${data.id}`)
      } else if (res.status === 401) {
        logout()
      }
    } catch (err) {
      console.error("Upload failed", err)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isMounted) return null

  return (
    <div className="min-h-screen bg-[#F8F7F4] relative overflow-hidden font-sans">
      <div className="fixed inset-0 -z-10 pointer-events-none opacity-40">
        <ParticleBackground />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-beige/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-charcoal flex items-center justify-center transition-transform duration-300 group-hover:scale-110 shadow-lg">
                <Sparkles className="w-5 h-5 text-cream" />
              </div>
              <span className="text-xl font-semibold text-charcoal tracking-tight">InsightAI</span>
            </Link>

            <div className="flex items-center gap-6">
              <Link 
                href="/" 
                className="flex items-center gap-2 text-sm text-warm-gray hover:text-charcoal transition-colors font-medium"
              >
                <ArrowLeft className="w-4 h-4" />
                Landing Page
              </Link>
              <div className="h-8 w-px bg-beige/50" />
              <button className="flex items-center gap-3 bg-white border border-beige/50 px-3 py-1.5 rounded-full shadow-sm hover:border-charcoal/30 transition-colors">
                <div className="w-6 h-6 rounded-full bg-accent-gold flex items-center justify-center text-charcoal">
                  {user?.full_name ? (
                    <span className="text-[10px] font-bold">{user.full_name[0]}</span>
                  ) : (
                    <User className="w-3.5 h-3.5" />
                  )}
                </div>
                <span className="text-xs font-semibold text-charcoal">{user?.full_name || "Guest"}</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto pt-32 pb-20 px-6 lg:px-8">
        {/* Welcome Header */}
        <header className="mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-4xl font-semibold text-charcoal font-display italic tracking-tight">
              Welcome back, <span className="text-accent-terra">{user?.full_name?.split(' ')[0] || "Analyst"}</span>
            </h1>
            <p className="text-warm-gray mt-2 text-lg">What would you like to uncover today?</p>
          </motion.div>
        </header>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Upload Zone (Large Bento Box) */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-2 relative group"
          >
            <div 
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                const file = e.dataTransfer.files[0];
                if (file) handleFileUpload(file);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "h-full min-h-[400px] bg-white rounded-[2.5rem] border-2 border-dashed transition-all duration-500 flex flex-col items-center justify-center p-12 cursor-pointer relative overflow-hidden",
                isDragging ? "border-accent-terra bg-accent-terra/5 scale-[0.99]" : "border-beige/50 hover:border-charcoal/30 hover:shadow-2xl hover:shadow-charcoal/5",
                isUploading && "pointer-events-none"
              )}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept=".csv" 
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
              />

              <div className="relative z-10 text-center space-y-6">
                <div className={cn(
                  "w-20 h-20 rounded-3xl bg-cream flex items-center justify-center mx-auto transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3 shadow-sm",
                  isDragging && "scale-110 rotate-6 bg-accent-terra/20"
                )}>
                  {isUploading ? (
                    <Loader2 className="w-10 h-10 text-accent-terra animate-spin" />
                  ) : (
                    <Upload className={cn("w-10 h-10 text-charcoal", isDragging && "text-accent-terra")} />
                  )}
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-2xl font-semibold text-charcoal">
                    {isUploading ? "Processing Dataset..." : "Upload new data"}
                  </h3>
                  <p className="text-warm-gray max-w-sm mx-auto">
                    Drag and drop your CSV file here, or click to browse your computer.
                  </p>
                </div>

                <div className="flex items-center justify-center gap-4 pt-4 text-xs font-medium text-warm-gray uppercase tracking-widest">
                  <span className="flex items-center gap-1.5"><Database className="w-3.5 h-3.5" /> CSV Only</span>
                  <span className="w-1 h-1 rounded-full bg-beige" />
                  <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5" /> Secure</span>
                  <span className="w-1 h-1 rounded-full bg-beige" />
                  <span className="flex items-center gap-1.5"><Zap className="w-3.5 h-3.5" /> AI Ready</span>
                </div>
              </div>

              {/* Background Decorative Elements */}
              <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-700">
                <div className="absolute top-10 right-10 w-32 h-32 bg-accent-gold/10 rounded-full blur-3xl" />
                <div className="absolute bottom-10 left-10 w-40 h-40 bg-accent-terra/10 rounded-full blur-3xl" />
              </div>
            </div>
          </motion.div>

          {/* Side Bento Column */}
          <div className="space-y-6">
            {/* Stats Card */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="bg-charcoal text-cream rounded-[2rem] p-8 relative overflow-hidden"
            >
              <div className="relative z-10">
                <BarChart3 className="w-8 h-8 text-accent-gold mb-4" />
                <h4 className="text-lg font-medium opacity-70">Total Analyses</h4>
                <div className="text-4xl font-bold mt-1">{recentAnalyses.length}</div>
                <div className="mt-6 flex items-center gap-2 text-sm text-accent-gold font-medium">
                  <span>View full history</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
              <div className="absolute -right-4 -bottom-4 w-32 h-32 bg-white/5 rounded-full blur-2xl" />
            </motion.div>

            {/* Recent Analysis List (Small Bento) */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="bg-white rounded-[2rem] border border-beige/50 p-8 flex-1 shadow-sm flex flex-col"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-warm-gray" />
                  <h3 className="font-semibold text-charcoal">Recent Activity</h3>
                </div>
                <button className="text-xs font-medium text-warm-gray hover:text-charcoal transition-colors">Clear</button>
              </div>

              <div className="space-y-4 flex-1">
                {isLoadingAnalyses ? (
                  <div className="flex flex-col items-center justify-center py-12 text-warm-gray space-y-3">
                    <Loader2 className="w-6 h-6 animate-spin opacity-20" />
                    <span className="text-xs uppercase tracking-tighter">Syncing...</span>
                  </div>
                ) : recentAnalyses.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center text-warm-gray opacity-50 space-y-3">
                    <History className="w-8 h-8 mx-auto" />
                    <p className="text-sm">No recent analyses found.</p>
                  </div>
                ) : (
                  recentAnalyses.slice(0, 4).map((analysis) => (
                    <button
                      key={analysis.id}
                      onClick={() => router.push(`/analysis/${analysis.id}`)}
                      className="w-full flex items-center gap-4 p-3 rounded-2xl hover:bg-cream transition-all group border border-transparent hover:border-beige/50 text-left"
                    >
                      <div className="w-10 h-10 rounded-xl bg-beige/30 flex items-center justify-center flex-shrink-0 group-hover:bg-white group-hover:shadow-sm transition-all">
                        <FileText className="w-5 h-5 text-warm-gray group-hover:text-accent-terra" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-charcoal truncate">{analysis.filename}</p>
                        <p className="text-[10px] text-warm-gray uppercase tracking-tighter mt-0.5">
                          {new Date(analysis.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-beige group-hover:text-charcoal transition-colors" />
                    </button>
                  ))
                )}
              </div>

              <button 
                onClick={() => router.push('/analysis')}
                className="mt-6 w-full py-3 rounded-2xl border border-beige/50 text-xs font-semibold text-charcoal hover:bg-cream transition-all flex items-center justify-center gap-2"
              >
                <Plus className="w-3.5 h-3.5" />
                Create New Analysis
              </button>
            </motion.div>
          </div>
        </div>

        {/* Action Grid (Bento Bottom) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
          {[
            { title: "Smart Cleaning", desc: "Automated data prep", icon: Zap, color: "text-blue-500" },
            { title: "Anomaly Detection", desc: "Spot hidden outliers", icon: AlertCircle, color: "text-red-500" },
            { title: "Deep Insights", desc: "AI-driven discovery", icon: Brain, color: "text-purple-500" },
            { title: "Export Data", desc: "Ready for reporting", icon: Download, color: "text-green-500" },
          ].map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 + (i * 0.1) }}
              className="bg-white rounded-[2rem] border border-beige/50 p-6 hover:shadow-lg hover:shadow-charcoal/5 transition-all group cursor-pointer"
            >
              <div className={cn("w-12 h-12 rounded-2xl bg-cream flex items-center justify-center mb-4 transition-transform group-hover:scale-110", item.color)}>
                <item.icon className="w-6 h-6" />
              </div>
              <h4 className="font-semibold text-charcoal text-sm">{item.title}</h4>
              <p className="text-xs text-warm-gray mt-1">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </main>
    </div>
  )
}
