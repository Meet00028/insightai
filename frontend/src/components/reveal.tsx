"use client"

import { useState, useEffect, useRef } from "react"
import { cn } from "@/lib/utils"

export function Reveal({ children, className, delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
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
    <div ref={ref} className={cn("transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)]", isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12", className)}>
      {children}
    </div>
  )
}
