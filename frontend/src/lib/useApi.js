import { useCallback, useEffect, useRef, useState } from "react";

import { request } from "./api";

// Small stale-while-revalidate cache so navigating back to a page shows the
// last result immediately while a fresh copy loads.
const cache = new Map();

export function invalidate(prefix = "") {
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) cache.delete(key);
  }
}

export function useApi(path, params, { enabled = true } = {}) {
  const key = path ? `${path}?${JSON.stringify(params || {})}` : null;
  const cached = key ? cache.get(key) : undefined;
  const [state, setState] = useState(() => ({
    data: cached?.data,
    total: cached?.total ?? null,
    error: null,
    loading: enabled && Boolean(path),
  }));
  const [nonce, setNonce] = useState(0);
  const paramsRef = useRef(params);
  paramsRef.current = params;

  useEffect(() => {
    if (!enabled || !path) {
      setState((current) => ({ ...current, loading: false }));
      return undefined;
    }
    const controller = new AbortController();
    const hit = cache.get(key);
    setState((current) => ({
      data: hit ? hit.data : current.data,
      total: hit ? hit.total : current.total,
      error: null,
      loading: true,
    }));
    request(path, { params: paramsRef.current, signal: controller.signal })
      .then(({ data, total }) => {
        cache.set(key, { data, total });
        setState({ data, total, error: null, loading: false });
      })
      .catch((error) => {
        if (error.name === "AbortError") return;
        setState((current) => ({ ...current, error, loading: false }));
      });
    return () => controller.abort();
  }, [key, path, enabled, nonce]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);

  return { ...state, reload, initialLoading: state.loading && state.data === undefined };
}

export function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
