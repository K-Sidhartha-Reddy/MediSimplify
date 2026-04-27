"use client";

import {
  createContext,
  createElement,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";
import type { User } from "@/lib/types";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  ready: boolean;
  setSession: (token: string, user: User) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const STORAGE_KEY = "mrs_auth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  const isValidStoredSession = (value: unknown): value is { token: string; user: User } => {
    if (!value || typeof value !== "object") return false;
    const parsed = value as Record<string, unknown>;
    const parsedUser = parsed.user as Record<string, unknown> | undefined;

    return (
      typeof parsed.token === "string" &&
      Boolean(parsedUser) &&
      typeof parsedUser?.id === "string" &&
      typeof parsedUser?.email === "string" &&
      typeof parsedUser?.full_name === "string" &&
      typeof parsedUser?.created_at === "string"
    );
  };

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as unknown;
        if (isValidStoredSession(parsed)) {
          setToken(parsed.token);
          setUser(parsed.user);
        } else {
          window.localStorage.removeItem(STORAGE_KEY);
        }
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }
    setReady(true);
  }, []);

  const setSession = (nextToken: string, nextUser: User) => {
    setToken(nextToken);
    setUser(nextUser);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: nextToken, user: nextUser }));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    window.localStorage.removeItem(STORAGE_KEY);
  };

  const value = useMemo(
    () => ({ token, user, ready, setSession, logout }),
    [token, user, ready]
  );

  return createElement(AuthContext.Provider, { value }, children);
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
