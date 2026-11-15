/**
 * Session token storage. The token lives in localStorage so a refresh keeps
 * you signed in; listeners let the auth provider react when the API reports
 * an expired session.
 */

const TOKEN_KEY = "budget-tracker.session";

type Listener = () => void;
const expiredListeners = new Set<Listener>();

export const session = {
  getToken(): string | null {
    if (typeof window === "undefined") return null;
    try {
      return window.localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  setToken(token: string): void {
    try {
      window.localStorage.setItem(TOKEN_KEY, token);
    } catch {
      /* storage unavailable (private mode): the session lasts for this tab only */
    }
  },
  clear(): void {
    try {
      window.localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  },
  onExpired(listener: Listener): () => void {
    expiredListeners.add(listener);
    return () => expiredListeners.delete(listener);
  },
  notifyExpired(): void {
    expiredListeners.forEach((listener) => listener());
  },
};
