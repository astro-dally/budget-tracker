"use client";

/**
 * Authentication state for the whole app. The token is the source of truth;
 * the user profile is loaded from /auth/me. Signing in or out clears the
 * query cache so one person's data can never flash up for another.
 */
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { session } from "@/lib/session";
import type { AuthResponse, User } from "@/lib/types";

type Status = "loading" | "authenticated" | "anonymous";

interface AuthContextValue {
  status: Status;
  user: User | null;
  /** True right after an explicit sign-out, so guards don't remember the last page. */
  signedOut: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (name: string, email: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const client = useQueryClient();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const [signedOut, setSignedOut] = useState(false);

  useEffect(() => {
    if (!session.getToken()) {
      setStatus("anonymous");
      return;
    }
    api.auth
      .me()
      .then((me) => {
        setUser(me);
        setStatus("authenticated");
      })
      .catch(() => {
        session.clear();
        setStatus("anonymous");
      });
  }, []);

  const signOut = useCallback(
    (message?: string) => {
      session.clear();
      client.clear();
      setSignedOut(!message);
      setUser(null);
      setStatus("anonymous");
      if (message) toast.info(message);
      router.replace("/login");
    },
    [client, router],
  );

  useEffect(
    () => session.onExpired(() => signOut("Your session ended. Sign in again to continue.")),
    [signOut],
  );

  const start = useCallback(
    (result: AuthResponse) => {
      client.clear();
      session.setToken(result.access_token);
      setSignedOut(false);
      setUser(result.user);
      setStatus("authenticated");
      return result.user;
    },
    [client],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      signedOut,
      login: async (email, password) => start(await api.auth.login(email, password)),
      register: async (name, email, password) => start(await api.auth.register(name, email, password)),
      logout: () => signOut(),
    }),
    [status, user, signedOut, start, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

/** Where to send someone after signing in. */
export function homeFor(user: User): string {
  return user.role === "admin" ? "/admin" : "/app";
}
