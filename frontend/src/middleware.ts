import NextAuth from "next-auth"
import { authConfig } from "./auth.config"

// We use "export default" here because the Next.js compiler understands it perfectly
export default NextAuth(authConfig).auth

export const config = {
  // Protects everything except API routes, static files, and images
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}