// Backend configuration
export const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8001";

// Helper for building API URLs
export function apiUrl(path: string): string {
  return `${BACKEND_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

// Helper for building WebSocket URLs (converts http(s) to ws(s))
export function wsUrl(path: string): string {
  const wsBase = BACKEND_URL.replace(/^http/, "ws");
  return `${wsBase}${path.startsWith("/") ? path : `/${path}`}`;
}
