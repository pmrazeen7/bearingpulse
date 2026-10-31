import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { getApiKey, onUnauthorized, request, setApiKey } from "./api";
import { invalidate } from "./useApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [key, setKey] = useState(getApiKey);
  const [expired, setExpired] = useState(false);

  const signOut = useCallback(() => {
    setApiKey("");
    invalidate();
    setKey("");
  }, []);

  const signIn = useCallback(async (candidate, { remember = false } = {}) => {
    const trimmed = candidate.trim();
    await request("/auth/verify", { key: trimmed });
    setApiKey(trimmed, { remember });
    invalidate();
    setExpired(false);
    setKey(trimmed);
  }, []);

  useEffect(
    () =>
      onUnauthorized(() => {
        setExpired(true);
        signOut();
      }),
    [signOut],
  );

  const value = useMemo(
    () => ({ isAuthenticated: Boolean(key), signIn, signOut, expired }),
    [key, signIn, signOut, expired],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
