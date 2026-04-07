"use client"

import React, { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Upload, Terminal, Sparkles, AlertCircle, CheckCircle2, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

interface AnalysisResult {
  insights: string[]
  anomalies: string[]
  strategy: string
}

interface DataAnalysisResponse {
  metadata: {
    row_count: number
    column_count: number
    [key: string]: unknown
  }
  ai_insights: AnalysisResult
}

type JobStartResponse = {
  job_id: string
  status: string
}

type JobStatusResponse =
  | { job_id: string; status: "PENDING" | "PROCESSING"; meta?: { message?: string } }
  | { job_id: string; status: "SUCCESS"; result: DataAnalysisResponse }
  | { job_id: string; status: "FAILED"; error: string }

export const AgenticTerminal: React.FC = () => {
  const router = useRouter()
  const { token, logout } = useAuth()
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [result, setResult] = useState<DataAnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobMessage, setJobMessage] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<"PENDING" | "PROCESSING" | "SUCCESS" | "FAILED" | null>(null)

  const loadingSteps = [
    "Initializing Agent...",
    "Uploading Data to Sandbox...",
    "Reading CSV Dataframes...",
    "Executing Statistical Analysis...",
    "Contextualizing with OpenAI GPT-4...",
    "Generating Insights...",
    "Finalizing Analysis Summary..."
  ]

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.type === "text/csv") {
      setFile(droppedFile)
      setError(null)
    } else {
      setError("Please upload a valid CSV file.")
    }
  }, [])

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setLoadingStep(0)
    setError(null)
    setResult(null)
    setJobId(null)
    setJobMessage(null)
    setJobStatus("PENDING")

    const interval = setInterval(() => {
      setLoadingStep((prev) => (prev < loadingSteps.length - 1 ? prev + 1 : prev))
    }, 1500)

    try {
      const headers: Record<string, string> = {}
      if (token) {
        headers["Authorization"] = `Bearer ${token}`
      }

      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analyze-data`, {
        method: "POST",
        body: formData,
        headers,
      })

      if (!response.ok) {
        let detail = `Failed to analyze data (HTTP ${response.status})`
        try {
          const errorBody = await response.json()
          if (errorBody?.detail) detail = String(errorBody.detail)
        } catch {}
        throw new Error(detail)
      }

      const start = await response.json()
      if (!start?.id) throw new Error("Missing analysis id from backend")
      setJobId(start.id)
      setJobStatus("PROCESSING")
      setJobMessage("Queued")

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
            throw new Error(`Failed to check status (HTTP ${statusResponse.status})`)
          }
          const sessionData = await statusResponse.json()

          if (sessionData.status === "completed") {
            clearInterval(interval)
            
            // Reconstruct the result format expected by the UI
            const reconstructedResult = {
              metadata: {
                row_count: sessionData.result_summary?.row_count || 0,
                column_count: sessionData.result_summary?.column_count || 0,
                column_names: sessionData.result_summary?.column_names || []
              },
              ai_insights: {
                insights: sessionData.insights || [],
                anomalies: sessionData.result_summary?.anomalies || [],
                strategy: sessionData.result_summary?.strategy || ""
              }
            }
            
            setResult(reconstructedResult)
            setIsUploading(false)
            setJobStatus("SUCCESS")
            setJobMessage(null)
            return
          }

          if (sessionData.status === "failed") {
            clearInterval(interval)
            setError(sessionData.error_message || "Analysis failed.")
            setIsUploading(false)
            setJobStatus("FAILED")
            return
          }

          // Continue polling if still running or queued
          setTimeout(poll, 2000)
        } catch (e: unknown) {
          clearInterval(interval)
          const message = e instanceof Error ? e.message : "Failed to check job status."
          setError(message)
          setIsUploading(false)
          setJobStatus("FAILED")
        }
      }

      poll()

    } catch (err: unknown) {
      clearInterval(interval)
      const message = err instanceof Error ? err.message : "Something went wrong."
      setError(message)
      setIsUploading(false)
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-8">
      {/* Upload Zone */}
      {!isUploading && !result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={onDrop}
          className={cn(
            "relative group cursor-pointer p-12 rounded-3xl border-2 border-dashed transition-all duration-500",
            file ? "border-charcoal bg-white shadow-elegant" : "border-beige hover:border-charcoal bg-cream/50"
          )}
          onClick={() => document.getElementById("file-upload")?.click()}
        >
          <input
            id="file-upload"
            type="file"
            className="hidden"
            accept=".csv"
            onChange={(e) => {
              const selectedFile = e.target.files?.[0]
              if (selectedFile) setFile(selectedFile)
            }}
          />
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className={cn(
              "w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-500",
              file ? "bg-charcoal text-white" : "bg-white text-charcoal shadow-sm"
            )}>
              <Upload className="w-8 h-8" />
            </div>
            <div className="text-center">
              <h3 className="text-xl font-semibold text-charcoal">
                {file ? file.name : "Upload your dataset"}
              </h3>
              <p className="text-warm-gray mt-1">
                Drag and drop your CSV here, or click to browse
              </p>
            </div>
            {file && (
              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                onClick={(e) => {
                  e.stopPropagation()
                  handleUpload()
                }}
                className="mt-6 px-8 py-3 bg-charcoal text-white rounded-full font-medium hover:bg-soft-black transition-all"
              >
                Analyze with AI Agent
              </motion.button>
            )}
          </div>
        </motion.div>
      )}

      {/* Terminal Loading State */}
      {isUploading && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-charcoal rounded-3xl overflow-hidden shadow-2xl border border-white/10"
        >
          <div className="px-6 py-4 bg-white/5 border-b border-white/10 flex items-center justify-between">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
              <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
              <div className="w-3 h-3 rounded-full bg-[#28c840]" />
            </div>
            <span className="text-xs font-mono text-cream/40 uppercase tracking-widest">
              Agentic Terminal{jobId ? ` • ${jobId.slice(0, 8)}` : ""}
            </span>
          </div>
          <div className="p-8 font-mono text-sm space-y-3 min-h-[300px]">
            {(jobStatus || jobMessage) && (
              <div className="flex items-center gap-3 text-cream/60">
                <ChevronRight className="w-4 h-4 text-accent-gold" />
                <span>{jobStatus || "PROCESSING"}{jobMessage ? ` — ${jobMessage}` : ""}</span>
              </div>
            )}
            {loadingSteps.slice(0, loadingStep + 1).map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-3"
              >
                <ChevronRight className="w-4 h-4 text-accent-gold" />
                <span className={cn(
                  i === loadingStep ? "text-cream" : "text-cream/40"
                )}>
                  {step}
                </span>
                {i === loadingStep && (
                  <motion.span
                    animate={{ opacity: [0, 1] }}
                    transition={{ repeat: Infinity, duration: 0.5 }}
                    className="w-2 h-4 bg-accent-gold"
                  />
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Result Cards */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid md:grid-cols-2 gap-8"
          >
            {/* Key Insights */}
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <Sparkles className="w-6 h-6 text-accent-gold" />
                <h2 className="text-2xl font-semibold text-charcoal font-display italic">Key Insights</h2>
              </div>
              <div className="grid gap-4">
                {result.ai_insights.insights.map((insight, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="p-6 bg-white rounded-3xl border border-beige hover:border-charcoal transition-all group"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-cream flex items-center justify-center text-charcoal group-hover:bg-charcoal group-hover:text-white transition-all">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                      <p className="text-charcoal/80 leading-relaxed pt-1">{insight}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Anomalies & Strategy */}
            <div className="space-y-8">
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-6 h-6 text-accent-terra" />
                  <h2 className="text-2xl font-semibold text-charcoal font-display italic">Data Anomalies</h2>
                </div>
                <div className="p-6 bg-white rounded-3xl border border-accent-terra/20">
                  <ul className="space-y-4">
                    {result.ai_insights.anomalies.map((anomaly, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-warm-gray">
                        <div className="w-1.5 h-1.5 rounded-full bg-accent-terra mt-1.5" />
                        {anomaly}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <Terminal className="w-6 h-6 text-charcoal" />
                  <h2 className="text-2xl font-semibold text-charcoal font-display italic">Analysis Strategy</h2>
                </div>
                <div className="p-6 bg-charcoal text-cream/90 rounded-3xl shadow-xl leading-relaxed text-sm">
                  {result.ai_insights.strategy}
                </div>
              </div>

              <button
                onClick={() => {
                  if (!jobId || !result) return
                  sessionStorage.setItem(`analysis:${jobId}`, JSON.stringify(result))
                  router.push(`/analysis/${jobId}`)
                }}
                className="w-full py-4 bg-charcoal text-white rounded-full font-medium hover:bg-soft-black transition-all"
              >
                Expand to Chat
              </button>

              <button
                onClick={() => {
                  setResult(null)
                  setFile(null)
                  setJobId(null)
                  setJobMessage(null)
                  setJobStatus(null)
                }}
                className="w-full py-4 border border-charcoal text-charcoal rounded-full font-medium hover:bg-charcoal hover:text-white transition-all"
              >
                Analyze Another Dataset
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm flex items-center gap-3"
        >
          <AlertCircle className="w-5 h-5" />
          {error}
        </motion.div>
      )}
    </div>
  )
}
