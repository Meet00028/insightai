import NextAuth from "next-auth" 
 import { authConfig } from "./auth.config" 
 
 // The middleware now verifies JWTs securely without touching Prisma! 
 export const { auth : middleware } = NextAuth(authConfig) 
 
 export const  config = { 
   // Protects everything except API routes, static files, and images 
   matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)" ], 
 } 
