import { API_BASE } from "@/lib/api";

type ErrorContext = Record<string, unknown>;

interface ClientErrorPayload {
  message: string;
  stack?: string;
  componentStack?: string;
  url?: string;
  userAgent?: string;
  userId?: string;
  context?: ErrorContext;
}

function currentUserId(): string | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    const raw = localStorage.getItem("user");
    if (!raw) return undefined;
    const parsed = JSON.parse(raw);
    return parsed?.id || parsed?.user_id || undefined;
  } catch {
    return undefined;
  }
}

/**
 * Report an unhandled client error to the backend sink.
 *
 * Best-effort: logs to console, then fires a keepalive fetch so navigation
 * does not cancel it. Never throws — logging must never crash the app.
 */
export function reportClientError(err: unknown, context?: ErrorContext): void {
  const e = err instanceof Error ? err : new Error(String(err));
  console.error("[client-error]", e, context);

  if (typeof window === "undefined") return;

  const payload: ClientErrorPayload = {
    message: e.message || "unknown error",
    stack: e.stack,
    componentStack:
      typeof context?.componentStack === "string"
        ? context.componentStack
        : undefined,
    url: window.location.href,
    userAgent: navigator.userAgent,
    userId: currentUserId(),
    context,
  };

  try {
    fetch(`${API_BASE}/client-errors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {
      /* sink errors silently */
    });
  } catch {
    /* sink errors silently */
  }
}
