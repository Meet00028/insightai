"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Send, Sparkles, AlertCircle, Terminal, History as HistoryIcon, Download, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/context/AuthContext"
import { motion, AnimatePresence } from "framer-motion"
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';
import { AnalysisSidebar } from "@/components/chat/AnalysisSidebar"

type AnalysisResult = {
  insights: string[]
  anomalies: string[]
  strategy: string
}

type DataAnalysisResponse = {
  metadata: {
    row_count: number
    column_count: number
    column_names?: string[]
    [key: string]: unknown
  }
  ai_insights: AnalysisResult
}

type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
}

export default function AnalysisDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { token, isLoading: isAuthLoading, logout } = useAuth()
  const analysisId = params?.id as string
  
  const [messages, setMessages] = useState<ChatMessage[]>(() => { 
      if (typeof window !== 'undefined' && analysisId) { 
        const saved = localStorage.getItem(`chat_${analysisId}`); 
        if (saved) return JSON.parse(saved); 
      } 
      return [{ id: "assistant-0", role: "assistant", content: "I am ready. Ask follow-up questions..." }]; 
    }); 

  useEffect(() => { 
    if (messages.length > 0) { 
      localStorage.setItem(`chat_${analysisId}`, JSON.stringify(messages)); 
    } 
  }, [messages, analysisId]);

  const [input, setInput] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isMounted, setIsMounted] = useState(false)
  const [analysisData, setAnalysisData] = useState<DataAnalysisResponse | null>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const chatEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => { setIsMounted(true) }, [])

  useEffect(() => {
    if (!analysisId || !isMounted || isAuthLoading) return

    const loadSessionData = async (isInitial = false) => {
      if (!token) return
      if (isInitial) setIsLoading(true)
      
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analysis/sessions/${analysisId}`, {
          headers: { "Authorization": `Bearer ${token}` },
        })

        if (response.ok) {
          const session = await response.json()
          console.log("Full Backend Response:", session)
          
          // --- THE ABSOLUTE FINAL MAPPING FIX ---
          // Use the worker's metadata first, then database fallback
          const newAnalysisData: DataAnalysisResponse = {
            metadata: {
              row_count: session.result_summary?.metadata?.row_count || session.dataset?.row_count || 0,
              column_count: session.result_summary?.metadata?.column_count || session.dataset?.column_count || 0,
              column_names: session.result_summary?.metadata?.column_names || session.dataset?.column_names || []
            },
            ai_insights: {
              insights: session.result_summary?.ai_insights?.insights || (Array.isArray(session.result_summary?.insights) ? session.result_summary.insights : []),
              anomalies: session.result_summary?.ai_insights?.anomalies || [],
              strategy: session.result_summary?.ai_insights?.strategy || session.result_summary?.strategy || ""
            }
          }
          
          setAnalysisData(newAnalysisData)
          
          // Only save to sessionStorage if we have actual data (row_count > 0)
          // This prevents overwriting valid cached data with empty "processing" state
          if (newAnalysisData.metadata.row_count > 0) {
            sessionStorage.setItem(`analysis:${analysisId}`, JSON.stringify(newAnalysisData))
          }
          
          // Only add initial query if we haven't started chatting yet
          const hasOnlyDefaultMessage = messages.length === 1 && messages[0].id === "assistant-0"
          if (session.query && (messages.length === 0 || hasOnlyDefaultMessage)) {
            setMessages([{ id: "user-initial", role: "user", content: session.query }])
          }

          const status = (session.status || '').toLowerCase()
          // Ensure polling stops on 'completed' or 'failed'
          if (status === 'completed' || status === 'failed') {
            if (pollingRef.current) {
              clearInterval(pollingRef.current)
              pollingRef.current = null
              console.log(`Polling stopped. Terminal status: ${status}`)
            }
          } else if (!pollingRef.current && isMounted) {
            // Start polling if not already polling and not terminal
            pollingRef.current = setInterval(() => loadSessionData(false), 3000)
          }
        } else if (response.status === 401) {
          logout()
        }
      } catch (err) {
        console.error("Fetch error:", err)
      } finally {
        if (isInitial) setIsLoading(false)
      }
    }

    loadSessionData(true)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [analysisId, isMounted, token, isAuthLoading])

  const data = useMemo<DataAnalysisResponse | null>(() => {
    if (analysisData) return analysisData
    if (!analysisId) return null
    try {
      const raw = sessionStorage.getItem(`analysis:${analysisId}`)
      if (!raw) return null
      return JSON.parse(raw) as DataAnalysisResponse
    } catch {
      return null
    }
  }, [analysisId, analysisData])

  const summary = useMemo(() => {
    if (!data) return null
    return {
      rows: data.metadata.row_count,
      cols: data.metadata.column_count,
      columns: Array.isArray(data.metadata.column_names) ? data.metadata.column_names : [],
      insights: data.ai_insights.insights || [],
      anomalies: data.ai_insights.anomalies || [],
      strategy: data.ai_insights.strategy || "",
    }
  }, [data])

  const displayMessages = useMemo<ChatMessage[]>(() => {
    return messages;
  }, [messages])

  const send = async () => {
    if (!input.trim() || !analysisId || isSending) return
    setIsSending(true)
    const userMsg = input.trim()
    setInput("")
    setMessages(p => [...p, { id: Date.now().toString(), role: "user", content: userMsg }])
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ 
          session_id: analysisId, 
          message: userMsg, 
          history: messages.map(m => ({ role: m.role, content: m.content })) 
        }),
      })
      const result = await response.json()
      setMessages(p => [...p, { id: (Date.now()+1).toString(), role: "assistant", content: result.reply }])
    } catch (err) { 
      console.error(err) 
    } finally { 
      setIsSending(false) 
    }
  }

  const handleDownload = (csvContent: string, filename: string = 'export.csv') => {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) { // feature detection
      link.setAttribute('href', URL.createObjectURL(blob));
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages.length])

  const renderMessageContent = (content: string) => { 
    try { 
      // 1. Try to parse the text as JSON 
      const parsedData = JSON.parse(content); 
      
      // 2. If it is chart data, render the Recharts component! 
      if (parsedData.is_chart_data && parsedData.type === 'bar') { 
        return ( 
          <div className="w-full h-64 mt-4 bg-white text-black p-4 rounded-lg shadow-sm border border-gray-200"> 
            <h4 className="text-center font-semibold mb-4">{parsedData.title}</h4> 
            <ResponsiveContainer width="100%" height="100%"> 
              <BarChart data={parsedData.data}> 
                <CartesianGrid strokeDasharray="3 3" opacity={0.5} /> 
                <XAxis dataKey={parsedData.xAxis} tick={{ fontSize: 12 }} /> 
                <YAxis tick={{ fontSize: 12 }} /> 
                <Tooltip /> 
                <Bar dataKey={parsedData.yAxis} fill="#000000" radius={[4, 4, 0, 0]} /> 
              </BarChart> 
            </ResponsiveContainer> 
          </div> 
        ); 
      } 
    } catch (e) { 
      // 3. If it fails to parse (because it's normal text), just return the text! 
    } 
    
    return <p className="whitespace-pre-wrap">{content}</p>; 
  }; 

  if (!isMounted) return null

  return (
    <div className="min-h-screen bg-cream flex">
      <AnalysisSidebar isOpen={isSidebarOpen} toggle={() => setIsSidebarOpen(!isSidebarOpen)} />
      
      <motion.div 
        animate={{ paddingLeft: isSidebarOpen ? 300 : 0 }} 
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="flex-1 min-w-0"
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between gap-4 mb-8">
            <div className="flex items-center gap-3">
              <button onClick={() => router.push("/analysis")} className="inline-flex items-center gap-2 text-sm text-warm-gray hover:text-charcoal transition-colors">
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <div className="h-5 w-px bg-beige" />
              <span className="text-sm text-warm-gray font-mono">analysis/{analysisId}</span>
            </div>
            <Link href="/" className="text-sm text-warm-gray hover:text-charcoal transition-colors">Home</Link>
          </div>

          {isLoading && !summary ? (
            <div className="flex flex-col items-center justify-center min-h-[400px] bg-white rounded-3xl border border-beige p-10">
              <Loader2 className="w-10 h-10 text-accent-terra animate-spin mb-4" />
              <p className="text-charcoal font-semibold text-xl">Initializing Analysis...</p>
            </div>
          ) : !summary ? (
            <div className="bg-white rounded-3xl border border-beige p-10 text-center">
              <p className="text-charcoal font-semibold text-xl">Session not found</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="bg-white rounded-3xl border border-beige p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <Sparkles className="w-6 h-6 text-accent-gold" />
                    <h1 className="text-2xl font-semibold text-charcoal font-display italic">Dataset Summary</h1>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-5 bg-cream rounded-2xl border border-beige">
                      <div className="text-xs text-warm-gray uppercase tracking-widest font-bold">Rows</div>
                      <div className="text-2xl font-semibold text-charcoal mt-2">{summary.rows.toLocaleString()}</div>
                    </div>
                    <div className="p-5 bg-cream rounded-2xl border border-beige">
                      <div className="text-xs text-warm-gray uppercase tracking-widest font-bold">Columns</div>
                      <div className="text-2xl font-semibold text-charcoal mt-2">{summary.cols.toLocaleString()}</div>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-3xl border border-beige p-8">
                  <h2 className="text-2xl font-semibold text-charcoal font-display italic mb-6">Initial Insights</h2>
                  <div className="space-y-4">
                    {summary.insights.length > 0 ? summary.insights.map((insight, i) => (
                      <div key={i} className="p-5 bg-cream rounded-2xl border border-beige text-charcoal/80">{insight}</div>
                    )) : <div className="text-warm-gray italic">AI is generating insights...</div>}
                  </div>
                </div>

                <div className="bg-white rounded-3xl border border-beige p-8">
                  <h2 className="text-2xl font-semibold text-charcoal font-display italic mb-6">Anomalies</h2>
                  <ul className="space-y-3">
                    {summary.anomalies.length > 0 ? summary.anomalies.map((a, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-warm-gray">
                        <span className="mt-2 w-1.5 h-1.5 rounded-full bg-accent-terra shrink-0" /> <span>{a}</span>
                      </li>
                    )) : <li className="text-warm-gray italic text-sm">No major anomalies detected yet.</li>}
                  </ul>
                </div>

                <div className="bg-charcoal rounded-3xl p-8 text-cream/90 shadow-xl">
                  <h2 className="text-2xl font-semibold text-cream font-display italic mb-6">Strategy</h2>
                  <div className="leading-relaxed text-sm">{summary.strategy || "Formulating strategic path..."}</div>
                </div>
              </div>

              <div className="bg-white rounded-3xl border border-beige overflow-hidden flex flex-col min-h-[600px] sticky top-8">
                <div className="px-6 py-4 bg-light-gray border-b border-beige flex items-center justify-between">
                  <div className="text-sm text-warm-gray font-mono">InsightAI Assistant</div>
                </div>
                <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-cream">
                  <AnimatePresence initial={false}>
                    {displayMessages.map((m) => (
                      <motion.div key={m.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
                        <div className={cn("max-w-[85%] rounded-3xl px-5 py-3 shadow-sm", m.role === "user" ? "bg-charcoal text-white" : "bg-white border border-beige text-charcoal")}>
                          {renderMessageContent(m.content)}
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  <div ref={chatEndRef} />
                </div>
                <div className="p-4 border-t border-beige bg-white">
                  <div className="flex items-end gap-3">
                    <textarea 
                      value={input} 
                      onChange={(e) => setInput(e.target.value)} 
                      onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} 
                      placeholder="Ask a follow-up question..." 
                      className="flex-1 resize-none rounded-2xl border border-beige bg-cream px-4 py-3 text-sm focus:outline-none" 
                      rows={2} 
                    />
                    <button onClick={send} disabled={isSending || !input.trim()} className="h-[44px] w-[44px] rounded-2xl bg-charcoal text-white flex items-center justify-center disabled:opacity-50 transition-colors">
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}
