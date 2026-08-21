"use client";

import { useMemo } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { createV2, type V2Client } from "@/lib/api-v2";

/** Client API v2 gắn với token hiện tại. */
export function useV2(): { api: V2Client | null; token: string | null } {
  const { token } = useAuth();
  const api = useMemo(() => (token ? createV2(token) : null), [token]);
  return { api, token };
}
