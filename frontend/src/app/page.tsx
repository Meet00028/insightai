"use client"

import { useEffect, useRef, useState, type ComponentType } from "react"
import Link from "next/link"
import { ArrowRight, Sparkles, Database, Brain, Shield, Zap, BarChart3, ChevronDown, Play, Check, Upload, Loader2, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"
import dynamic from "next/dynamic"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { useAuth } from "@/context/AuthContext"

const ParticleBackground = dynamic(() => import("@/components/ParticleBackground").then(mod => mod.ParticleBackground), { 
  ssr: false 
})

const AiAgentTerminal = dynamic(() => import("@/components/AiAgentTerminal").then(mod => mod.AiAgentTerminal), { 
  ssr: false 
})

// Animated Counter
function AnimatedCounter({ end, duration = 2000, suffix = "" }: { end: number; duration?: number; suffix?: string }) {
  const [count, setCount] = useState(0)
  const [mounted, setMounted] = useState(false)
  const countRef = useRef<HTMLSpanElement>(null)
  const hasAnimated = useRef(false)

  useEffect(() => {
    setMounted(true)
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true
          let startTime: number
          const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const progress = Math.min((timestamp - startTime) / duration, 1)
            setCount(Math.floor(progress * end))
            if (progress < 1) requestAnimationFrame(animate)
          }
          requestAnimationFrame(animate)
        }
      },
      { threshold: 0.5 }
    )
    if (countRef.current) observer.observe(countRef.current)
    return () => observer.disconnect()
  }, [end, duration])

  return <span ref={countRef}>{mounted ? count.toLocaleString() : count}{suffix}</span>
}

// Reveal on Scroll
function Reveal({ children, className, delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setTimeout(() => setIsVisible(true), delay) },
      { threshold: 0.1 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [delay])

  return (
    <div ref={ref} className={cn("transition-all duration-1000 ease-expo-out", isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12", className)}>
      {children}
    </div>
  )
}

// Feature Card
function FeatureCard({ icon: Icon, title, description }: { icon: ComponentType<{ className?: string }>; title: string; description: string }) {
  const [isHovered, setIsHovered] = useState(false)
  return (
    <div
      className="group relative p-8 bg-white rounded-3xl border border-beige transition-all duration-500 hover:border-charcoal hover:shadow-elegant cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={cn("absolute inset-0 bg-gradient-to-br from-cream to-beige rounded-3xl opacity-0 transition-opacity duration-500", isHovered && "opacity-100")} />
      <div className="relative z-10">
        <div className={cn("w-14 h-14 rounded-2xl bg-cream flex items-center justify-center mb-6 transition-all duration-500", isHovered && "bg-charcoal scale-110")}>
          <Icon className={cn("w-6 h-6 transition-colors duration-500", isHovered ? "text-white" : "text-charcoal")} />
        </div>
        <h3 className="text-xl font-semibold mb-3 text-charcoal">{title}</h3>
        <p className="text-warm-gray leading-relaxed">{description}</p>
        <div className={cn("mt-6 flex items-center gap-2 text-charcoal font-medium transition-all duration-500", isHovered ? "translate-x-2" : "translate-x-0")}>
          <span className="text-sm">Learn more</span>
          <ArrowRight className={cn("w-4 h-4 transition-transform duration-500", isHovered && "translate-x-1")} />
        </div>
      </div>
    </div>
  )
}

// Testimonial Card
function TestimonialCard({ quote, author, role, company }: { quote: string; author: string; role: string; company: string }) {
  return (
    <div className="p-8 bg-white rounded-3xl border border-beige hover:border-charcoal transition-all duration-500">
      <div className="flex gap-1 mb-6">
        {[...Array(5)].map((_, i) => <Sparkles key={i} className="w-4 h-4 text-accent-gold fill-accent-gold" />)}
      </div>
      <p className="text-lg text-charcoal leading-relaxed mb-6 font-display italic">&ldquo;{quote}&rdquo;</p>
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-beige to-cream flex items-center justify-center text-charcoal font-semibold">{author[0]}</div>
        <div>
          <p className="font-semibold text-charcoal">{author}</p>
          <p className="text-sm text-warm-gray">{role} at {company}</p>
        </div>
      </div>
    </div>
  )
}

const features = [
  { icon: Brain, title: "AI-Powered Analysis", description: "Our intelligent agent analyzes your data, identifies patterns, and generates actionable insights automatically." },
  { icon: Zap, title: "Real-time Processing", description: "Watch the AI think in real-time with our streaming interface. See every step of the analysis as it happens." },
  { icon: Shield, title: "Secure Execution", description: "All code runs in isolated Docker containers, ensuring maximum security for your sensitive data." },
  { icon: BarChart3, title: "Beautiful Visualizations", description: "Generate stunning charts and graphs automatically from your data insights with one click." },
  { icon: Database, title: "Smart Data Cleaning", description: "Automatically detect and fix data quality issues with AI-powered cleaning pipelines." },
  { icon: Sparkles, title: "Natural Language", description: "Ask questions about your data in plain English. No SQL or coding knowledge required." },
]

const testimonials = [
  { quote: "InsightAI transformed how we approach data analysis. What used to take our team days now happens in minutes.", author: "Sarah Chen", role: "Chief Data Officer", company: "TechVentures" },
  { quote: "The AI agent is incredibly intuitive. I can ask complex questions and get actionable insights immediately.", author: "Michael Ross", role: "Product Manager", company: "StartupXYZ" },
  { quote: "Best investment we've made this year. The automated cleaning pipelines alone saved us countless hours.", author: "Emily Watson", role: "Analytics Lead", company: "DataDriven Inc" },
]

const pricingPlans = [
  {
    name: "Starter",
    price: "$0",
    description: "Perfect for individuals and small projects.",
    features: ["1 GB Storage", "5 Datasets/month", "Basic AI Analysis", "Standard Support"],
    cta: "Get started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$49",
    description: "Advanced tools for data professionals.",
    features: ["10 GB Storage", "Unlimited Datasets", "Advanced AI Agent", "Priority Support", "Custom Visualizations"],
    cta: "Start free trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "Scaling data power for large organizations.",
    features: ["Unlimited Storage", "Dedicated Instance", "SLA Guarantee", "Custom Integrations", "24/7 Phone Support"],
    cta: "Contact sales",
    highlighted: false,
  },
]

export default function LandingPage() {
  const [scrollY, setScrollY] = useState(0)
  const { user, token, logout } = useAuth()
  const isLoggedIn = !!token
  const [showLogoutModal, setShowLogoutModal] = useState(false)

  const handleLogout = () => {
    logout()
  }

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY)
    window.addEventListener("scroll", handleScroll, { passive: true })
    
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-cream relative overflow-hidden">
      {/* Background Layers */}
      <div className="fixed inset-0 -z-20 bg-cream" />
      <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden">
        <ParticleBackground />
      </div>

      <div className="relative z-10 bg-transparent">
        {/* Navigation */}
        <nav className={cn("fixed top-0 left-0 right-0 z-50 transition-all duration-500", scrollY > 100 ? "bg-cream/90 backdrop-blur-xl border-b border-beige" : "bg-transparent")}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-charcoal flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                <Sparkles className="w-5 h-5 text-cream" />
              </div>
              <span className="text-xl font-semibold text-charcoal tracking-tight">InsightAI</span>
            </Link>

            <div className="hidden md:flex items-center gap-8">
              {["Features", "How it works", "Testimonials", "Pricing"].map((item) => (
                <a key={item} href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} className="text-sm text-warm-gray hover:text-charcoal transition-colors underline-animation font-medium">{item}</a>
              ))}
            </div>

            <div className="flex items-center gap-4">
              {isLoggedIn ? (
                <div className="flex items-center gap-3">
                  <Link 
                    href="/analysis" 
                    className="px-5 py-2.5 bg-black text-white text-sm font-medium rounded-full hover:bg-soft-black transition-all duration-300 hover:scale-105 hover:shadow-lg flex items-center gap-2"
                  >
                    Go to Dashboard
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                  <button
                    onClick={() => setShowLogoutModal(true)}
                    className="p-2.5 text-warm-gray hover:text-charcoal hover:bg-beige/50 rounded-full transition-all duration-300"
                    title="Sign Out"
                  >
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              ) : (
                <>
                  <Link href="/login" className="hidden sm:block text-sm text-warm-gray hover:text-charcoal transition-colors font-medium">Sign in</Link>
                  <Link href="/register" className="px-5 py-2.5 bg-black text-white text-sm font-medium rounded-full hover:bg-soft-black transition-all duration-300 hover:scale-105 hover:shadow-lg">Get started</Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-20 overflow-hidden">
        <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8 py-20">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8 text-left">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full border border-beige shadow-sm">
                <Sparkles className="w-4 h-4 text-accent-gold" />
                <span className="text-sm text-warm-gray font-medium">AI-Powered Analytics</span>
              </div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-semibold text-charcoal leading-[1.1] tracking-tight">
                Turn data into <span className="font-display italic text-accent-terra">insights</span> with AI
              </h1>

              <p className="text-lg text-warm-gray max-w-lg leading-relaxed">
                Upload your data, ask questions in plain English, and let our AI agent analyze, visualize, and uncover patterns automatically.
              </p>

              <div className="flex flex-wrap gap-4 pt-4">
                <Link 
                  href={isLoggedIn ? "/analysis" : "/register"} 
                  className="group px-8 py-4 bg-black text-white rounded-full font-medium transition-all duration-300 hover:bg-soft-black hover:scale-105 hover:shadow-xl flex items-center gap-3"
                >
                  {isLoggedIn ? "Go to Dashboard" : "Start free trial"}
                  <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" />
                </Link>
                <button className="group px-8 py-4 border border-black text-charcoal rounded-full font-medium transition-all duration-300 hover:bg-black hover:text-white flex items-center gap-3">
                  <Play className="w-4 h-4" />
                  Watch demo
                </button>
              </div>

              <div className="flex gap-12 pt-12 border-t border-beige">
                <div><p className="text-3xl font-semibold text-charcoal"><AnimatedCounter end={50000} suffix="+" /></p><p className="text-sm text-warm-gray mt-1">Datasets analyzed</p></div>
                <div><p className="text-3xl font-semibold text-charcoal"><AnimatedCounter end={99} suffix="%" /></p><p className="text-sm text-warm-gray mt-1">Accuracy rate</p></div>
                <div><p className="text-3xl font-semibold text-charcoal"><AnimatedCounter end={10} suffix="x" /></p><p className="text-sm text-warm-gray mt-1">Faster analysis</p></div>
              </div>
            </div>

            <div className="relative">
              <AiAgentTerminal />
              <div className="absolute -top-6 -right-6 w-24 h-24 bg-accent-gold/20 rounded-full blur-2xl opacity-50" />
              <div className="absolute -bottom-6 -left-6 w-32 h-32 bg-accent-terra/20 rounded-full blur-2xl opacity-50" />
            </div>
          </div>
        </div>

        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-warm-gray opacity-50">
          <span className="text-xs uppercase tracking-widest font-medium">Scroll to explore</span>
          <ChevronDown className="w-5 h-5 animate-bounce" />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-32 bg-transparent relative">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <Reveal className="text-center mb-20">
            <span className="text-sm uppercase tracking-widest text-warm-gray mb-4 block font-medium">Features</span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-semibold text-charcoal max-w-3xl mx-auto leading-tight tracking-tight">
              Everything you need for <span className="font-display italic text-accent-terra">data analysis</span>
            </h2>
          </Reveal>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Reveal key={feature.title} delay={index * 100}>
                <FeatureCard {...feature} />
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-32 bg-transparent relative">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-20 items-center">
            <div className="text-left">
              <Reveal>
                <span className="text-sm uppercase tracking-widest text-warm-gray mb-4 block font-medium">How it works</span>
                <h2 className="text-4xl sm:text-5xl font-semibold text-charcoal mb-12 leading-tight tracking-tight">
                  Three simple steps to <span className="font-display italic text-accent-terra">insights</span>
                </h2>
              </Reveal>

              <div className="space-y-8">
                {[
                  { step: "01", title: "Upload your data", desc: "Drag and drop your CSV files. We support files up to 100MB with automatic validation." },
                  { step: "02", title: "Ask a question", desc: "Type your question in plain English. No SQL or coding knowledge required." },
                  { step: "03", title: "Get insights", desc: "Watch the AI analyze your data in real-time and generate actionable insights." }
                ].map((item, index) => (
                  <Reveal key={item.step} delay={index * 150}>
                    <div className="flex gap-6 group">
                      <div className="flex-shrink-0 w-14 h-14 rounded-2xl bg-white border border-beige flex items-center justify-center group-hover:bg-charcoal group-hover:border-charcoal transition-all duration-300 shadow-sm">
                        <span className="text-lg font-semibold text-warm-gray group-hover:text-white transition-colors">{item.step}</span>
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold text-charcoal mb-2">{item.title}</h3>
                        <p className="text-warm-gray leading-relaxed">{item.desc}</p>
                      </div>
                    </div>
                  </Reveal>
                ))}
              </div>
            </div>

            <Reveal delay={300}>
              <div className="relative">
                <div className="aspect-square bg-white rounded-3xl border border-beige p-8 flex items-center justify-center shadow-elegant">
                  <div className="w-full max-w-sm space-y-4">
                    <div className="p-4 bg-cream rounded-xl border border-beige animate-float shadow-sm">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-charcoal flex items-center justify-center"><Database className="w-5 h-5 text-white" /></div>
                        <div><p className="text-sm font-medium text-charcoal">sales_data.csv</p><p className="text-xs text-warm-gray">2.4 MB • 50K rows</p></div>
                      </div>
                    </div>
                    <div className="p-4 bg-cream rounded-xl border border-beige animate-float ml-8 shadow-sm" style={{ animationDelay: "0.5s" }}>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-accent-terra flex items-center justify-center"><Brain className="w-5 h-5 text-white" /></div>
                        <div><p className="text-sm font-medium text-charcoal">AI Analysis</p><p className="text-xs text-warm-gray">Processing...</p></div>
                      </div>
                    </div>
                    <div className="p-4 bg-cream rounded-xl border border-beige animate-float shadow-sm" style={{ animationDelay: "1s" }}>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-accent-gold flex items-center justify-center"><BarChart3 className="w-5 h-5 text-white" /></div>
                        <div><p className="text-sm font-medium text-charcoal">Insights Ready</p><p className="text-xs text-warm-gray">12 findings discovered</p></div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="absolute -top-4 -right-4 w-24 h-24 bg-accent-gold/10 rounded-full blur-2xl opacity-50" />
                <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-accent-terra/10 rounded-full blur-2xl opacity-50" />
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-32 bg-transparent relative">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <Reveal className="text-center mb-20">
            <span className="text-sm uppercase tracking-widest text-warm-gray mb-4 block font-medium">Testimonials</span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-semibold text-charcoal max-w-3xl mx-auto leading-tight tracking-tight">
              Loved by data <span className="font-display italic text-accent-terra">professionals</span>
            </h2>
          </Reveal>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Reveal key={testimonial.author} delay={index * 150}>
                <TestimonialCard {...testimonial} />
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-32 bg-transparent border-t border-beige relative">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <Reveal className="text-center mb-20">
            <span className="text-sm uppercase tracking-widest text-warm-gray mb-4 block font-medium">Pricing</span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-semibold text-charcoal max-w-3xl mx-auto leading-tight tracking-tight">
              Simple, transparent <span className="font-display italic text-accent-terra">pricing</span>
            </h2>
          </Reveal>

          <div className="grid md:grid-cols-3 gap-8 items-stretch">
            {pricingPlans.map((plan, index) => (
              <div key={plan.name} className="h-full">
                <div className={cn(
                  "p-8 rounded-[2rem] border transition-all duration-500 flex flex-col h-full",
                  plan.highlighted 
                    ? "bg-black border-black text-white shadow-2xl scale-105 z-10" 
                    : "bg-white border-beige text-charcoal hover:border-charcoal shadow-sm"
                )}>
                  <div className="mb-8">
                    <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold tracking-tight">{plan.price}</span>
                      {plan.price !== "Custom" && <span className={cn("text-sm", plan.highlighted ? "text-cream/60" : "text-warm-gray")}>/month</span>}
                    </div>
                    <p className={cn("mt-4 text-sm leading-relaxed", plan.highlighted ? "text-cream/70" : "text-warm-gray")}>
                      {plan.description}
                    </p>
                  </div>

                  <ul className="space-y-4 mb-8 flex-1">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-3 text-sm">
                        <Check className={cn("w-4 h-4 flex-shrink-0", plan.highlighted ? "text-accent-gold" : "text-accent-terra")} />
                        <span className={plan.highlighted ? "text-cream/90" : "text-charcoal/90"}>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Link 
                      href={isLoggedIn ? "/analysis" : "/register"}
                      className={cn(
                        "w-full py-4 rounded-full font-semibold transition-all duration-300 text-center",
                        plan.highlighted 
                          ? "bg-white text-charcoal hover:bg-cream" 
                          : "bg-black text-white hover:bg-soft-black"
                      )}
                    >
                      {isLoggedIn ? "Go to Dashboard" : plan.cta}
                    </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 bg-charcoal relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-accent-gold rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-accent-terra rounded-full blur-[100px] translate-y-1/2 -translate-x-1/2" />
        </div>
        <div className="relative z-10 max-w-4xl mx-auto px-6 lg:px-8 text-center">
          <Reveal>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-semibold text-cream mb-6 leading-tight tracking-tight">
              Ready to transform <span className="font-display italic text-accent-gold">your data?</span>
            </h2>
          </Reveal>
          <Reveal delay={150}>
            <p className="text-lg text-cream/70 mb-10 max-w-2xl mx-auto leading-relaxed">
              Start your free trial today. No credit card required. Experience the power of AI-driven analytics.
            </p>
          </Reveal>
          <Reveal delay={300}>
            <div className="flex flex-wrap justify-center gap-4">
              <Link 
                href={isLoggedIn ? "/analysis" : "/register"} 
                className="group px-8 py-4 bg-cream text-charcoal rounded-full font-semibold hover:bg-white hover:scale-105 transition-all duration-300 flex items-center gap-3"
              >
                {isLoggedIn ? "Go to Dashboard" : "Get started free"}
                <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" />
              </Link>
              <button className="px-8 py-4 border border-cream/30 text-cream rounded-full font-semibold hover:bg-cream/10 transition-all duration-300">
                Talk to sales
              </button>
            </div>
          </Reveal>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 bg-transparent border-t border-beige">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2 text-left">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-charcoal flex items-center justify-center shadow-sm">
                  <Sparkles className="w-5 h-5 text-cream" />
                </div>
                <span className="text-xl font-semibold text-charcoal tracking-tight">InsightAI</span>
              </div>
              <p className="text-warm-gray max-w-sm leading-relaxed">
                AI-powered data analytics platform that transforms how businesses understand and act on their data.
              </p>
            </div>
            <div className="text-left">
              <h4 className="font-semibold text-charcoal mb-4">Product</h4>
              <ul className="space-y-3">
                {["Features", "Pricing", "API", "Integrations"].map((item) => (
                  <li key={item}><a href="#" className="text-sm text-warm-gray hover:text-charcoal transition-colors underline-animation">{item}</a></li>
                ))}
              </ul>
            </div>
            <div className="text-left">
              <h4 className="font-semibold text-charcoal mb-4">Company</h4>
              <ul className="space-y-3">
                {["About", "Blog", "Careers", "Contact"].map((item) => (
                  <li key={item}><a href="#" className="text-sm text-warm-gray hover:text-charcoal transition-colors underline-animation">{item}</a></li>
                ))}
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-beige flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-warm-gray font-medium">© 2024 InsightAI. All rights reserved.</p>
            <div className="flex gap-6">
              {["Privacy", "Terms", "Security"].map((item) => (
                <a key={item} href="#" className="text-sm text-warm-gray hover:text-charcoal transition-colors font-medium">{item}</a>
              ))}
            </div>
          </div>
        </div>
      </footer>

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
              <p className="text-warm-gray mb-8">Are you sure you want to sign out? You will need to sign in again to access your dashboard.</p>
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
    </div>
    </div>
  )
}
