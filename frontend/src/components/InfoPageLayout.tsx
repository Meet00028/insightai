import Link from "next/link"
import { ArrowLeft, Sparkles } from "lucide-react"

export function InfoPageLayout({ title, children }: { title: string, children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-cream selection:bg-charcoal selection:text-cream">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-cream/80 backdrop-blur-xl border-b border-beige">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-charcoal flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                <Sparkles className="w-5 h-5 text-cream" />
              </div>
              <span className="text-xl font-semibold text-charcoal tracking-tight">InsightAI</span>
            </Link>
            <Link href="/" className="text-sm text-warm-gray hover:text-charcoal transition-colors flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </Link>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-20 px-6 lg:px-8 max-w-4xl mx-auto">
        <h1 className="text-4xl sm:text-5xl font-semibold text-charcoal mb-8 tracking-tight">{title}</h1>
        <div className="prose prose-charcoal max-w-none text-warm-gray leading-relaxed space-y-6">
          {children}
        </div>
      </main>

      <footer className="py-12 border-t border-beige text-center">
        <p className="text-sm text-warm-gray">© 2024 InsightAI. All rights reserved.</p>
      </footer>
    </div>
  )
}
