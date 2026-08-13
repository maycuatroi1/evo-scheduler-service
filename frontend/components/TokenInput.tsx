"use client";

import { useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";

export function TokenInput() {
  const { token, setToken, isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");

  if (isAuthenticated && !open) {
    return (
      <div className="flex items-center gap-2">
        <span className="rounded bg-accent/15 px-2 py-1 text-xs font-semibold text-accent">
          Đã xác thực
        </span>
        <button
          type="button"
          onClick={() => setToken(null)}
          className="rounded-md border border-border px-2 py-1 text-xs font-semibold text-foreground hover:bg-destructive hover:text-white"
        >
          Đăng xuất
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {open ? (
        <>
          <input
            type="password"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Dán JWT (Bearer token)"
            className="w-64 rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground focus:border-primary focus:outline-none"
          />
          <button
            type="button"
            onClick={() => {
              setToken(draft.trim() || null);
              setOpen(false);
              setDraft("");
            }}
            className="rounded-md bg-primary px-3 py-1 text-xs font-semibold text-white hover:opacity-90"
          >
            Lưu
          </button>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              setDraft("");
            }}
            className="rounded-md border border-border px-2 py-1 text-xs font-semibold text-foreground hover:bg-primary/10"
          >
            Hủy
          </button>
        </>
      ) : (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-md border border-border px-3 py-1 text-xs font-semibold text-foreground hover:bg-primary/10"
        >
          Dán token
        </button>
      )}
    </div>
  );
}
