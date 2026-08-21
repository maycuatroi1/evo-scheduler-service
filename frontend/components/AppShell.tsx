"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/providers/AuthProvider";
import { Sidebar } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";

const PUBLIC_PATHS = ["/login", "/register"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { token, user, isAuthenticated, ready, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    // Chờ đọc xong phiên đã lưu rồi mới kết luận là chưa đăng nhập, nếu
    // không mỗi lần tải lại trang sẽ bị đá về trang đăng nhập.
    if (ready && !token && !isPublic) {
      router.replace("/login");
    }
  }, [ready, token, isPublic, router]);

  if (isPublic) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        {children}
      </main>
    );
  }

  if (!ready) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6 text-foreground-3">
        Đang khôi phục phiên làm việc…
      </main>
    );
  }

  if (!token) {
    return null;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-end gap-3 border-b border-border px-6 py-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <span className="rounded bg-accent/15 px-2 py-1 text-xs font-semibold text-accent">
                {user.email}
              </span>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-border px-2 py-1 text-xs font-semibold text-foreground hover:bg-destructive hover:text-white"
              >
                Đăng xuất
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="rounded-md bg-primary px-3 py-1 text-xs font-semibold text-white hover:opacity-90"
            >
              Đăng nhập
            </Link>
          )}
          <ThemeToggle />
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
