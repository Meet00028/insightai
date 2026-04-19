import type { NextAuthConfig } from "next-auth" 
 
 export const  authConfig = { 
   session: { strategy: "jwt"  }, 
   trustHost: true , 
   secret : process.env.AUTH_SECRET, 
   providers: [], // Keep empty here so Edge doesn't panic 
   callbacks : { 
     async session({ session, token })  { 
       if  (token.sub && session.user) { 
         session.user.id = token.sub 
       } 
       return  session 
     }, 
   }, 
 } satisfies NextAuthConfig 
