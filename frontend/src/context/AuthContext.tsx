"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { ApiClient } from "@/services/apiClient";

export interface AuthUser {
  username: string;
  full_name: string;
  email?: string;
  role: "admin" | "viewer" | string;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; message?: string }>;
  logout: () => Promise<void>;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_STORAGE_KEY = "smartsched_auth_token";
const USER_STORAGE_KEY = "smartsched_auth_user";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const savedToken = typeof window !== "undefined" ? localStorage.getItem(TOKEN_STORAGE_KEY) : null;
    const savedUserRaw = typeof window !== "undefined" ? localStorage.getItem(USER_STORAGE_KEY) : null;

    if (savedToken && savedUserRaw) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUserRaw));
      } catch {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
      }
    }

    // Verify active session with backend if token exists
    if (savedToken) {
      ApiClient.get<AuthUser>("/auth/me")
        .then((me) => {
          setUser(me);
          localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(me));
        })
        .catch(() => {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          localStorage.removeItem(USER_STORAGE_KEY);
          setToken(null);
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const res = await ApiClient.post<{
        access_token: string;
        token_type: string;
        role: string;
        username: string;
        full_name: string;
      }>("/auth/login", { username, password });

      const loggedInUser: AuthUser = {
        username: res.username,
        full_name: res.full_name,
        role: res.role,
      };

      localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(loggedInUser));
      setToken(res.access_token);
      setUser(loggedInUser);
      return { success: true };
    } catch (err: any) {
      return { success: false, message: err.message || "Invalid username or password." };
    }
  };

  const logout = async () => {
    try {
      await ApiClient.post("/auth/logout");
    } catch {
      // Ignore network errors on logout
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
      }
      setToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        isAdmin: user?.role === "admin",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
