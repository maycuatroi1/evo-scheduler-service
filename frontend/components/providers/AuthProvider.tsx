"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { authLogin, authRegister, type AuthUser } from "@/lib/api";

type AuthContextValue = {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  ready: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (
    name: string,
    email: string,
    password: string,
  ) => Promise<AuthUser>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "xeptkb.session";

/** Phiên đăng nhập lưu trong sessionStorage: sống qua lần tải lại trang
 *  nhưng mất khi đóng tab, nên token không nằm lại trên máy dùng chung. */
type Stored = { token: string; user: AuthUser };

function readStored(): Stored | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as Stored;
    if (!data?.token || !data?.user?.email) return null;
    return data;
  } catch {
    return null;
  }
}

function writeStored(data: Stored | null) {
  if (typeof window === "undefined") return;
  try {
    if (data) window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    else window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* chế độ riêng tư có thể chặn ghi — bỏ qua, phiên vẫn dùng được */
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  // Chưa đọc xong phiên đã lưu thì chưa được kết luận là chưa đăng nhập,
  // nếu không AppShell sẽ đẩy về trang đăng nhập ngay khi tải lại trang.
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = readStored();
    if (stored) {
      setToken(stored.token);
      setUser(stored.user);
    }
    setReady(true);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authLogin({ email, password });
    setToken(res.token);
    setUser(res.user);
    writeStored({ token: res.token, user: res.user });
    return res.user;
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      const res = await authRegister({ name, email, password });
      setToken(res.token);
      setUser(res.user);
      writeStored({ token: res.token, user: res.user });
      return res.user;
    },
    [],
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    writeStored(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: token !== null,
      ready,
      login,
      register,
      logout,
    }),
    [token, user, ready, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth phải nằm trong AuthProvider");
  return ctx;
}
