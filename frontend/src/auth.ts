import NextAuth from "next-auth" 
 import { PrismaAdapter } from "@auth/prisma-adapter" 
 import { db } from "@/lib/db" 
 import GitHub from "next-auth/providers/github" 
 import Google from "next-auth/providers/google" 
 import Credentials from "next-auth/providers/credentials" 
 import bcrypt from "bcrypt" 
 import { authConfig } from "./auth.config" 
 
 export const  { handlers, auth, signIn, signOut } = NextAuth({ 
   ...authConfig, // Inherit the safe edge configuration 
   adapter : PrismaAdapter(db), 
   providers : [ 
     Google({ 
       clientId: process.env.AUTH_GOOGLE_ID as string , 
       clientSecret: process.env.AUTH_GOOGLE_SECRET as string , 
     }), 
     GitHub({ 
       clientId: process.env.AUTH_GITHUB_ID as string , 
       clientSecret: process.env.AUTH_GITHUB_SECRET as string , 
     }), 
     Credentials({ 
       name: "Credentials" , 
       credentials : { 
         email: { label: "Email", type: "email"  }, 
         password: { label: "Password", type: "password"  }, 
       }, 
       async authorize(credentials)  { 
         if (!credentials?.email || !credentials?.password) return null 
 
         const user = await  db.user.findUnique({ 
           where: { email: credentials.email as string  }, 
         }) 
 
         if (!user || !user.hashed_password) return null 
 
         const isPasswordValid = await  bcrypt.compare( 
           credentials.password as string , 
           user.hashed_password 
         ) 
 
         if (!isPasswordValid) return null 
 
         return  { 
           id : user.id, 
           email : user.email, 
           name : user.full_name, 
         } 
       }, 
     }), 
   ], 
 }) 
