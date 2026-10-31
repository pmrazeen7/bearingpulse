import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { AlertTriangle, Check, Info, X } from "lucide-react";

const ToastContext = createContext(null);
const ICONS = { success: Check, error: X, warning: AlertTriangle, info: Info };

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const dismiss = useCallback((id) => {
    setToasts((items) => items.map((item) => (item.id === id ? { ...item, leaving: true } : item)));
    setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 220);
  }, []);

  const push = useCallback(
    (tone, title, text, duration = tone === "error" ? 6500 : 4000) => {
      idRef.current += 1;
      const id = idRef.current;
      setToasts((items) => [...items.slice(-3), { id, tone, title, text, duration }]);
      setTimeout(() => dismiss(id), duration);
      return id;
    },
    [dismiss],
  );

  const api = useMemo(
    () => ({
      success: (title, text) => push("success", title, text),
      error: (title, text) => push("error", title, text),
      warning: (title, text) => push("warning", title, text),
      info: (title, text) => push("info", title, text),
      dismiss,
    }),
    [push, dismiss],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-region" role="region" aria-label="Notifications" aria-live="polite">
        {toasts.map((toast) => {
          const Icon = ICONS[toast.tone];
          return (
            <div key={toast.id} className={`toast toast-${toast.tone} ${toast.leaving ? "is-leaving" : ""}`} role="status">
              <span className="toast-icon">
                <Icon aria-hidden="true" />
              </span>
              <div>
                <div className="toast-title">{toast.title}</div>
                {toast.text && <div className="toast-text">{toast.text}</div>}
              </div>
              <button type="button" className="toast-close" aria-label="Dismiss" onClick={() => dismiss(toast.id)}>
                <X size={14} />
              </button>
              <span className="toast-progress" style={{ animationDuration: `${toast.duration}ms` }} />
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside <ToastProvider>");
  return context;
}
