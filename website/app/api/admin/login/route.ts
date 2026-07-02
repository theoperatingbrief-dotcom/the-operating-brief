import { NextRequest, NextResponse } from "next/server";
import { getAdminSecret } from "../auth";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const { password } = await request.json();
  const adminPassword = getAdminSecret();

  if (!adminPassword || password !== adminPassword) {
    return NextResponse.json({ error: "Invalid password" }, { status: 401 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set("admin_auth", adminPassword, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    maxAge: 60 * 60 * 24 * 7, // 7 days
    sameSite: "strict",
    path: "/",
  });
  return response;
}
