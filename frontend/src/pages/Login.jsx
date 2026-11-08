import React, { useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Eye, EyeOff, KeyRound } from "lucide-react";

import { Mascot } from "../components/Mascot";
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
  const [shake, setShake] = useState(false);
  const target = location.state?.from || "/app";

  useEffect(() => {
    document.title = "Sign in · BearingPulse";
  }, []);

  if (isAuthenticated) return <Navigate to={target} replace />;

  const submit = async (event) => {
    event.preventDefault();
    if (!value.trim()) {
      setError("Enter the API key configured as API_KEY on the server.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await signIn(value, { remember });
      navigate(target, { replace: true });
    } catch (err) {
      setError(err.status === 401 ? "That API key was rejected by the server." : err.message);
      setShake(true);
      setTimeout(() => setShake(false), 450);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth">
      <div className="landing-bg" aria-hidden="true">
        <div className="landing-grid" />
        <div className="blob blob-1" />
        <div className="blob blob-2" />
      </div>
      <div className={`auth-card ${shake ? "is-shaking" : ""}`}>
        <div className="auth-mascot">
          <Mascot mood={error ? "worried" : "idle"} size={96} />
        </div>
        <h1>Sign in to BearingPulse</h1>
        <p className="auth-sub">Use the API key from your server's environment to open the dashboard.</p>
        <form onSubmit={submit} noValidate>
          {expired && !error && <Notice tone="warning">Your session expired or the key changed. Please sign in again.</Notice>}
          {error && <Notice tone="danger">{error}</Notice>}
          <Field label="API key" htmlFor="api-key" hint="Sent as the X-API-Key header on every request.">
            <div className="input-group">
              <KeyRound aria-hidden="true" />
              <input
                id="api-key"
                className="input"
                style={{ paddingRight: 40 }}
                type={reveal ? "text" : "password"}
                autoComplete="off"
                spellCheck={false}
                autoFocus
                value={value}
                aria-invalid={Boolean(error)}
                onChange={(event) => setValue(event.target.value)}
                placeholder="Paste API key"
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
            Remember on this device
          </label>
          <Button type="submit" variant="primary" size="lg" loading={busy}>
            Sign in
          </Button>
        </form>
        <div className="auth-foot">
          <Link to="/" className="row" style={{ justifyContent: "center" }}>
            <ArrowLeft size={14} /> Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
