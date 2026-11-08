import React, { useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";

import { Logo } from "../components/Logo";
import { Button, Field, Notice } from "../components/ui";
import { useAuth } from "../lib/auth";

export default function Login() {
  const { isAuthenticated, signIn, expired } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [value, setValue] = useState("");
  const [remember, setRemember] = useState(false);
  const [reveal, setReveal] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const target = location.state?.from || "/app";

  useEffect(() => {
    document.title = "Sign in · BearingPulse";
  }, []);

  if (isAuthenticated) return <Navigate to={target} replace />;

  const submit = async (event) => {
    event.preventDefault();
    if (!value.trim()) {
      setError("Enter the API key set as API_KEY on the server.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await signIn(value, { remember });
      navigate(target, { replace: true });
    } catch (err) {
      setError(err.status === 401 ? "The server rejected that API key." : err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth">
      <div className="auth-card">
        <Link to="/" aria-label="BearingPulse home" className="auth-logo">
          <Logo />
        </Link>
        <h1>Sign in</h1>
        <p className="auth-sub">Enter the API key from your server's .env file.</p>
        <form onSubmit={submit} noValidate>
          {expired && !error && <Notice tone="warning">Your session ended or the key changed. Sign in again.</Notice>}
          {error && <Notice tone="danger">{error}</Notice>}
          <Field label="API key" htmlFor="api-key" hint="Sent as the X-API-Key header with every request.">
            <div className="input-group">
              <input
                id="api-key"
                className="input"
                style={{ paddingLeft: 12, paddingRight: 40 }}
                type={reveal ? "text" : "password"}
                autoComplete="off"
                spellCheck={false}
                autoFocus
                value={value}
                aria-invalid={Boolean(error)}
                onChange={(event) => setValue(event.target.value)}
              />
              <button
                type="button"
                className="btn btn-ghost btn-sm btn-icon"
                style={{ position: "absolute", right: 3 }}
                aria-label={reveal ? "Hide key" : "Show key"}
                onClick={() => setReveal((v) => !v)}
              >
                {reveal ? <EyeOff /> : <Eye />}
              </button>
            </div>
          </Field>
          <label className="checkbox">
            <input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} />
            Keep me signed in on this device
          </label>
          <Button type="submit" variant="primary" loading={busy}>
            Sign in
          </Button>
        </form>
      </div>
    </div>
  );
}
