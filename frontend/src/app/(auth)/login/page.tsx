"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Eye, EyeOff, Mail, Lock, ArrowRight, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"
import { signIn } from "next-auth/react"
import { useAuth } from "@/context/AuthContext"
import dynamic from "next/dynamic"

const ParticleBackground = dynamic(() => import("@/components/ParticleBackground").then(mod => mod.ParticleBackground), { 
  ssr: false 
})

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      const formData = new FormData()
      formData.append("username", email)
      formData.append("password", password)

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/login`, {
        method: "POST",
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Invalid credentials. Please try again.")
      }

      // Use the login function from AuthContext to set token and user data
      login(data.access_token, data.user)

      // Redirect to analysis page
      router.push("/analysis")
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSocialLogin = async (provider: string) => {
    try {
      await signIn(provider, { callbackUrl: "/analysis" })
    } catch {
      setError(`Failed to sign in with ${provider}`)
    }
  }

  return (
    <div className="min-h-screen bg-cream flex overflow-hidden">
      {/* Background Layers */}
      <div className="fixed inset-0 -z-20 bg-cream" />
      <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden">
        <ParticleBackground />
      </div>

      {/* Left Side - Form */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="flex-1 flex flex-col justify-center px-8 sm:px-12 lg:px-20 xl:px-32"
      >
        <div className="max-w-md w-full mx-auto">
          {/* Logo */}
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mb-12"
          >
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-12 h-12 rounded-2xl bg-charcoal flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                <Sparkles className="w-6 h-6 text-cream" />
              </div>
              <span className="text-2xl font-semibold text-charcoal">InsightAI</span>
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <h1 className="text-4xl font-semibold text-charcoal mb-3">Welcome back</h1>
            <p className="text-warm-gray mb-8">Sign in to continue your data journey</p>
          </motion.div>

          {/* Social Login */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="grid grid-cols-2 gap-4 mb-6"
          >
            <button 
              onClick={() => handleSocialLogin("google")}
              className="flex items-center justify-center gap-3 px-4 py-3 bg-white border border-beige rounded-xl text-charcoal hover:border-charcoal hover:bg-cream transition-all duration-300 shadow-sm"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              <span className="text-sm font-medium">Google</span>
            </button>
            <button 
              onClick={() => handleSocialLogin("github")}
              className="flex items-center justify-center gap-3 px-4 py-3 bg-white border border-beige rounded-xl text-charcoal hover:border-charcoal hover:bg-cream transition-all duration-300 shadow-sm"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.11.825-.26.825-.58 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
              <span className="text-sm font-medium">GitHub</span>
            </button>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="relative mb-6"
          >
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-beige" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-4 bg-cream text-sm text-warm-gray">or continue with email</span>
            </div>
          </motion.div>

          {/* Form */}
          <motion.form 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            onSubmit={handleSubmit} 
            className="space-y-5"
          >
            {error && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm"
              >
                {error}
              </motion.div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium text-charcoal">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-warm-gray" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-12 pr-4 py-3.5 bg-white border border-beige rounded-xl text-charcoal placeholder:text-warm-gray focus:outline-none focus:border-charcoal focus:ring-2 focus:ring-charcoal/10 transition-all duration-300"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-charcoal">Password</label>
                <Link href="/forgot-password" className="text-sm text-warm-gray hover:text-charcoal transition-colors underline-animation">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-warm-gray" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-12 pr-12 py-3.5 bg-white border border-beige rounded-xl text-charcoal placeholder:text-warm-gray focus:outline-none focus:border-charcoal focus:ring-2 focus:ring-charcoal/10 transition-all duration-300"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-warm-gray hover:text-charcoal transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                "w-full flex items-center justify-center gap-2 px-6 py-4 bg-charcoal text-white rounded-xl font-medium transition-all duration-300",
                isLoading ? "opacity-70 cursor-not-allowed" : "hover:bg-soft-black hover:scale-[1.02] hover:shadow-lg"
              )}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Sign in
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </motion.form>

          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="mt-8 text-center text-warm-gray"
          >
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-charcoal font-medium hover:underline underline-animation">
              Create one
            </Link>
          </motion.p>
        </div>
      </motion.div>

      {/* Right Side - Decorative & Particles */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.3 }}
        className="hidden lg:flex lg:w-1/2 bg-charcoal relative overflow-hidden"
      >
        <div className="absolute inset-0 w-full h-full pointer-events-none">
          <ParticleBackground />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-16 xl:px-24">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="space-y-8"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-md rounded-full border border-white/10">
              <Sparkles className="w-4 h-4 text-accent-gold" />
              <span className="text-sm text-cream/80">AI-Powered Analytics</span>
            </div>

            <h2 className="text-4xl xl:text-5xl font-semibold text-cream leading-tight tracking-tight">
              Transform your data into{" "}
              <span className="font-display italic text-accent-gold">actionable insights</span>
            </h2>

            <p className="text-lg text-cream/70 max-w-md leading-relaxed">
              Join thousands of data professionals who trust InsightAI to uncover patterns and drive decisions.
            </p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 pt-8 border-t border-white/10">
              <div>
                <p className="text-3xl font-semibold text-cream">50K+</p>
                <p className="text-sm text-cream/60 mt-1">Datasets</p>
              </div>
              <div>
                <p className="text-3xl font-semibold text-cream">99%</p>
                <p className="text-sm text-cream/60 mt-1">Accuracy</p>
              </div>
              <div>
                <p className="text-3xl font-semibold text-cream">10x</p>
                <p className="text-sm text-cream/60 mt-1">Speed</p>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  )
}
