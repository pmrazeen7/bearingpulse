import React, { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";

import { PageHeader } from "../components/StatCard";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, ErrorState, Field, Notice, SkeletonRows } from "../components/ui";
import { api } from "../lib/api";
import { ASIN_PATTERN, formatRelative } from "../lib/format";
import { invalidate, useApi } from "../lib/useApi";
import { CRAWL_JOBS, useCrawl } from "../layouts/AppLayout";

export default function Settings() {
  const toast = useToast();
  const crawl = useCrawl();
  const configs = useApi("/alerts/config");
  const health = useApi("/health");
  const [threshold, setThreshold] = useState("5");
  const [asin, setAsin] = useState("");
  const [email, setEmail] = useState("");
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [running, setRunning] = useState("");

  useEffect(() => {
    const base = configs.data?.find((c) => c.scope === "default");
    if (base && !asin) { setThreshold(String(base.threshold_pct)); setEmail(base.alert_email || ""); }
  }, [configs.data]); // eslint-disable-line react-hooks/exhaustive-deps

  const save = async (event) => {
    event.preventDefault();
    const next = {};
    const value = Number(threshold);
    if (!threshold || Number.isNaN(value) || value <= 0 || value > 100) next.threshold = "Enter a percentage between 0 and 100.";
    if (asin && !ASIN_PATTERN.test(asin.toUpperCase())) next.asin = "ASINs are 10 letters or digits.";
    if (email && !/^\S+@\S+\.\S+$/.test(email)) next.email = "Enter a valid email address.";
    setErrors(next);
    if (Object.keys(next).length) return;
    setBusy(true);
    try {
      await api.post("/alerts/config", { threshold_pct: value, asin_id: asin || null, alert_email: email || null });
      invalidate("/alerts/config");
      configs.reload();
      toast.success("Threshold saved", asin ? `Override applied to ${asin.toUpperCase()}.` : "Default threshold updated.");
      setAsin("");
    } catch (err) {
      if (err.status === 404) setErrors({ asin: err.message }); else toast.error("Could not save", err.message);
    } finally { setBusy(false); }
  };

  const remove = async (scope) => {
    try { await api.delete(`/alerts/config/${scope}`); invalidate("/alerts/config"); configs.reload(); toast.success("Override removed", `${scope} now uses the default threshold.`); }
    catch (err) { toast.error("Could not remove override", err.message); }
  };

  const run = async (job) => { setRunning(job); await crawl(job); setRunning(""); };
  const h = health.data;

  return (
    <div className="page">
      <PageHeader title="Settings" subtitle="Alert thresholds, background jobs and system status." />
      <div className="grid-2-even">
        <Card title="Alert thresholds" subtitle="Raise a price-drop alert when the Buy Box price falls by more than this percentage.">
          <form className="stack" onSubmit={save} noValidate>
            <Field label="Threshold (%)" htmlFor="threshold" error={errors.threshold}>
              <input id="threshold" className="input num" inputMode="decimal" value={threshold} aria-invalid={Boolean(errors.threshold)} onChange={(e) => setThreshold(e.target.value)} />
            </Field>
            <Field label="Apply to ASIN (optional)" htmlFor="asin" error={errors.asin} hint="Leave blank to set the default for all products.">
              <input id="asin" className="input mono" maxLength={10} placeholder="B07XYZ1234" value={asin} aria-invalid={Boolean(errors.asin)} onChange={(e) => setAsin(e.target.value.toUpperCase())} />
            </Field>
            <Field label="Notification email (optional)" htmlFor="email" error={errors.email} hint="Stored with the threshold. Delivery uses the SMTP settings on the server.">
              <input id="email" className="input" type="email" value={email} aria-invalid={Boolean(errors.email)} onChange={(e) => setEmail(e.target.value)} />
            </Field>
            <div><Button type="submit" variant="primary" loading={busy}>Save threshold</Button></div>
          </form>
        </Card>
        <Card title="Saved thresholds" flush>
          {configs.initialLoading ? <SkeletonRows rows={3} columns={3} /> : configs.error ? <ErrorState compact error={configs.error} onRetry={configs.reload} /> : (
            <ul className="feed">{configs.data?.map((c) => (
              <li key={c.scope}>
                {c.scope === "default" ? <Badge tone="accent">Default</Badge> : <span className="asin-chip">{c.scope}</span>}
                <span className="feed-main"><strong className="num">{c.threshold_pct}%</strong><span className="subtle">{c.updated_at ? `updated ${formatRelative(c.updated_at)}` : "from server environment"}</span></span>
                {c.scope !== "default" && <Button size="sm" variant="ghost" icon={Trash2} aria-label={`Remove override for ${c.scope}`} onClick={() => remove(c.scope)} />}
              </li>))}</ul>
          )}
        </Card>
      </div>
      <Card title="Background jobs" subtitle="Scheduled automatically by Celery beat. Trigger any of them on demand.">
        <div className="job-grid">{CRAWL_JOBS.map((j) => (
          <div className="job" key={j.job}><div><strong>{j.label}</strong><p className="muted">{j.hint}</p></div><Button loading={running === j.job} onClick={() => run(j.job)}>Run now</Button></div>
        ))}</div>
      </Card>
      <Card title="System status">
        {h ? (
          <div className="row" style={{ gap: 20, flexWrap: "wrap" }}>
            {[["API", "ok"], ["Database", h.db], ["Redis / queue", h.redis]].map(([name, status]) => (
              <span className="row" key={name}><span className={`live-dot ${status === "ok" ? "" : "is-down"}`} />{name}: <strong>{status}</strong></span>
            ))}
            <span className="subtle">v{h.version}</span>
          </div>
        ) : health.error ? <Notice tone="danger">{health.error.message}</Notice> : <SkeletonRows rows={1} columns={3} />}
      </Card>
    </div>
  );
}
