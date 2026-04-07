"use client"

import React, { useState, useRef, useEffect } from "react"
import { Brain, Database, BarChart3, Upload, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"

export function AiAgentTerminal() {
  const router = useRouter()
  const { token, logout } = useAuth()
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [insights, setInsights] = useState<string[] | null>(null)
  const [metadata, setMetadata] = useState<{ rows: number, cols: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isExiting, setIsExiting] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [result, setResult] = useState<any | null>(null)
  const [mounted, setMounted] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleUploadClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!token) {
      router.push('/login'); // Redirect guests immediately
      return;
    }
    // Trigger file input for logged-in users
    document.getElementById("file-upload")?.click() || fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return
    
    setFile(selectedFile)
    setError(null)
    setInsights(null)
    setIsAnalyzing(true)
    setJobId(null)
    setResult(null)
    
    const headers: Record<string, string> = {}
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
    
    const formData = new FormData()
    formData.append("file", selectedFile)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analyze-data`, {
        method: "POST",
        body: formData,
        headers,
      })

      if (!response.ok) {
        if (response.status === 401) {
          logout()
          return
        }
        let detail = `Analysis failed (HTTP ${response.status})`
        try {
          const errorBody = await response.json()
          if (errorBody?.detail) detail = String(errorBody.detail)
        } catch {}
        throw new Error(detail)
      }

      const start = await response.json()
      if (!start?.id) throw new Error("Missing analysis id from backend")
      setJobId(start.id)

      const poll = async () => {
        try {
          const pollHeaders: Record<string, string> = {}
          if (token) {
            pollHeaders["Authorization"] = `Bearer ${token}`
          }

          const statusResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analysis/sessions/${start.id}`, {
            headers: pollHeaders,
          })
          if (!statusResponse.ok) {
            if (statusResponse.status === 401) {
              logout()
              return
            }
            throw new Error(`Failed to check job status (HTTP ${statusResponse.status})`)
          }
          const sessionData = await statusResponse.json()

          if (sessionData.status === "completed") {
            const summary = sessionData.result_summary || {};
            const meta = summary.metadata || {};
            const ai = summary.ai_insights || {};

            const reconstructedResult = {
              metadata: {
                row_count: meta.row_count || 0,
                column_count: meta.column_count || 0,
                column_names: meta.column_names || []
              },
              ai_insights: {
                insights: ai.insights || [],
                anomalies: ai.anomalies || [],
                strategy: ai.strategy || ""
              }
            };
            
            setMetadata({ rows: reconstructedResult.metadata.row_count, cols: reconstructedResult.metadata.column_count });
            setInsights(reconstructedResult.ai_insights.insights);
            setResult(reconstructedResult);
            setIsAnalyzing(false);
            return;
          }

          if (sessionData.status === "failed") {
            setError(sessionData.error_message || "Failed to analyze data. Check your backend.")
            setIsAnalyzing(false)
            return
          }

          setTimeout(poll, 2000)
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : "Failed to analyze data. Check your backend."
          setError(message)
          setIsAnalyzing(false)
        }
      }

      poll()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to analyze data. Check your backend."
      setError(message)
      setIsAnalyzing(false)
    }
  }

  return (
    <div className={cn(
      "relative bg-white rounded-3xl border border-beige shadow-elegant overflow-hidden transition-all duration-500",
      isExiting && "scale-[1.02] shadow-2xl z-50"
    )}>
      <AnimatePresence>
        {isExiting && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-black z-50 flex items-center justify-center"
          >
            <Loader2 className="w-8 h-8 text-white animate-spin" />
          </motion.div>
        )}
      </AnimatePresence>
      <div className="px-6 py-4 bg-light-gray border-b border-beige flex items-center justify-between">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
          <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
          <div className="w-3 h-3 rounded-full bg-[#28c840]" />
        </div>
        <span className="text-sm text-warm-gray font-mono">AI Agent Terminal</span>
        <button 
          onClick={handleUploadClick}
          className="text-xs font-medium text-charcoal hover:text-soft-black flex items-center gap-1"
        >
          <Upload className="w-3 h-3" />
          Upload CSV
        </button>
        <input type="file" ref={fileInputRef} className="hidden" accept=".csv" onChange={handleFileChange} />
      </div>
      <div 
        className="relative p-6 font-mono text-sm space-y-4 bg-charcoal text-cream min-h-[400px]"
        onClick={handleUploadClick}
      >
        {!file && !isAnalyzing && !insights && (
          <div className="flex flex-col items-center justify-center h-[300px] text-cream/40">
            <Database className="w-12 h-12 mb-4 opacity-20" />
            <p>Waiting for dataset upload...</p>
          </div>
        )}

        {file && (
          <div className="flex items-start gap-3 animate-fade-in-up">
            <Database className="w-5 h-5 text-accent-terra flex-shrink-0 mt-0.5" />
            <div><span className="text-accent-terra">loading</span><p className="mt-1 text-cream/80">Selected: {file.name}</p></div>
          </div>
        )}

        {isAnalyzing && (
          <div className="flex items-start gap-3 animate-fade-in-up">
            <Loader2 className="w-5 h-5 text-accent-gold flex-shrink-0 mt-0.5 animate-spin" />
            <div><span className="text-accent-gold">analyzing</span><p className="mt-1 text-cream/80">Running deep statistical analysis...</p></div>
          </div>
        )}

        {insights && (
          <>
            <div className="flex items-start gap-3 animate-fade-in-up">
              <Brain className="w-5 h-5 text-accent-gold flex-shrink-0 mt-0.5" />
              <div><span className="text-accent-gold">processing complete</span><p className="mt-1 text-cream/80">Detected {mounted ? metadata?.rows.toLocaleString() : metadata?.rows} rows × {metadata?.cols} columns</p></div>
            </div>
            <div className="flex items-start gap-3 animate-fade-in-up">
              <BarChart3 className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="text-green-400">insights found</span>
                <ul className="mt-2 space-y-2">
                  {insights.map((insight, i) => (
                    <li key={i} className="text-cream/80 leading-relaxed">• {insight}</li>
                  ))}
                </ul>
              </div>
            </div>
          </>
        )}

        {error && <div className="text-red-400 mt-4">Error: {error}</div>}
        
        <div className="flex items-center gap-2 text-cream/40 mt-8"><span className="animate-pulse">_</span></div>

        {mounted && jobId && result && (
          <button 
            onClick={(e) => { 
              e.stopPropagation(); // This stops the file picker from opening again! 
              if (jobId && result) { 
                sessionStorage.setItem(`analysis:${jobId}`, JSON.stringify(result)); 
                router.push(`/analysis/${jobId}`); 
              } 
            }} 
            className="absolute bottom-4 right-4 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/15 border border-white/10 text-xs text-cream/80 transition-colors z-10 cursor-pointer" 
          > 
            Expand 
          </button>
        )}
      </div>
    </div>
  )
}
