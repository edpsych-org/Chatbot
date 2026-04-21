import { NextRequest, NextResponse } from "next/server";

// Redirect root to /login for every HTTP method (GET, POST, probes, etc.).
// Handling this in middleware avoids the Next.js app-router "Failed to find
// Server Action" error that fires when a POST hits a page component without a
// next-action header (stale clients, health checks, bots).
export function middleware(req: NextRequest) {
  if (req.nextUrl.pathname === "/") {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url, 307);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/"],
};
