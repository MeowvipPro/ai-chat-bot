import React, { createContext, useContext, useEffect, useState } from "react";
import { getMeApi, loginApi, registerApi } from "../services/auth";
import type { UserResponse, LoginData, RegisterData } from "../services/auth";

interface AuthContextType {
  user: UserResponse | null;
  loading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      getMeApi()
        .then(setUser)
        .catch(() => {
          // Token is invalid/expired — clear silently, don't trigger refresh loop
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (data: LoginData) => {
    const tokens = await loginApi(data);
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    const me = await getMeApi();
    setUser(me);
  };

  const register = async (data: RegisterData) => {
    await registerApi(data);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
