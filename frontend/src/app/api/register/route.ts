import { NextResponse } from "next/server"
import bcrypt from "bcrypt"
import { db } from "@/lib/db"

export async function POST(req: Request) {
  try {
    const { name, email, password } = await req.json()

    if (!name || !email || !password) {
      return NextResponse.json(
        { message: "Missing required fields" },
        { status: 400 }
      )
    }

    const existingUser = await db.users.findUnique({
      where: { email },
    })

    if (existingUser) {
      return NextResponse.json(
        { message: "Email already in use" },
        { status: 400 }
      )
    }

    const hashedPassword = await bcrypt.hash(password, 10)

    const user = await db.users.create({
      data: {
        id: crypto.randomUUID(),
        full_name: name,
        email,
        hashed_password: hashedPassword,
        is_active: true,
        is_verified: false,
        is_superuser: false,
        subscription_tier: "FREE",
        created_at: new Date(),
        updated_at: new Date(),
      },
    })

    return NextResponse.json(
      { message: "User created successfully", userId: user.id },
      { status: 201 }
    )
  } catch (error) {
    console.error("Registration error:", error)
    return NextResponse.json(
      { message: "Internal server error" },
      { status: 500 }
    )
  }
}
