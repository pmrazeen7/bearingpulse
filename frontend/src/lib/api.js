// Thin fetch wrapper around the FastAPI backend.
// The API key is entered by the operator at sign-in and kept in browser
// storage; it is never compiled into the bundle.

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
// Interactive docs exist only in development (the API hides them in production),
// unless a docs URL is configured explicitly.
export const DOCS_URL = import.meta.env.VITE_API_DOCS_URL || (import.meta.env.DEV ? "/docs" : "");

const STORAGE_KEY = "bp.apiKey";
let apiKey = readStoredKey();
const unauthorizedListeners = new Set();

function readStoredKey() {
  try {
    return sessionStorage.getItem(STORAGE_KEY) || localStorage.getItem(STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

export function getApiKey() {
  return apiKey;
}

export function setApiKey(key, { remember = false } = {}) {
  apiKey = key || "";
  try {
    sessionStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_KEY);
    if (apiKey) {
      (remember ? localStorage : sessionStorage).setItem(STORAGE_KEY, apiKey);
    }
  } catch {
    // Storage can be unavailable (private mode); the key still lives in memory.
  }
}

export function onUnauthorized(listener) {
  unauthorizedListeners.add(listener);
  return () => unauthorizedListeners.delete(listener);
}

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function describe(detail, status) {
  if (!detail) return `Request failed (${status})`;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(".") : "";
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .join("; ");
  }
  return `Request failed (${status})`;
}

function buildUrl(path, params) {
  const url = `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  if (!params) return url;
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  });
  const qs = query.toString();
  return qs ? `${url}?${qs}` : url;
}

export async function request(path, { method = "GET", params, body, signal, key, raw = false } = {}) {
  let response;
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      signal,
      headers: {
        Accept: raw ? "*/*" : "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...((key ?? apiKey) ? { "X-API-Key": key ?? apiKey } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError("Cannot reach the API. Check that the backend is running.", 0);
  }

  if (response.status === 401 && key === undefined) {
    unauthorizedListeners.forEach((listener) => listener());
  }

  if (!response.ok) {
    let detail;
    try {
      detail = (await response.json()).detail;
    } catch {
      detail = undefined;
    }
    throw new ApiError(describe(detail, response.status), response.status, detail);
  }

  if (raw) return response;
  if (response.status === 204) return { data: null, total: null };
  const data = await response.json();
  const totalHeader = response.headers.get("X-Total-Count");
  return { data, total: totalHeader !== null ? Number(totalHeader) : null };
}

export const api = {
  get: (path, params, options) => request(path, { ...options, params }).then((result) => result.data),
  list: (path, params, options) => request(path, { ...options, params }),
  post: (path, body, options) => request(path, { ...options, method: "POST", body }).then((r) => r.data),
  patch: (path, body, options) => request(path, { ...options, method: "PATCH", body }).then((r) => r.data),
  delete: (path, options) => request(path, { ...options, method: "DELETE" }).then((r) => r.data),
};

export async function downloadFile(path, params, fallbackName) {
  const response = await request(path, { params, raw: true });
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = match ? match[1] : fallbackName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
