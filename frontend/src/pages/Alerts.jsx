import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check, CheckCheck, Download, RefreshCw, Undo2 } from "lucide-react";

import { PageHeader } from "../components/StatCard";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, ErrorState, Pagination, Segmented, SkeletonRows } from "../components/ui";
import { api, downloadFile } from "../lib/api";
import { ALERT_TYPES, formatCurrency, formatDateTime, formatRelative } from "../lib/format";
import { invalidate, useApi } from "../lib/useApi";

const PAGE_SIZE = 20;
const TYPES = [{ value: "", label: "All" }, ...Object.entries(ALERT_TYPES).map(([value, meta]) => ({ value, label: meta.label }))];
const STATES = [{ value: "open", label: "Open" }, { value: "done", label: "Acknowledged" }, { value: "all", label: "All" }];

function describe(alert) {
  if (alert.alert_type === "price_drop") return `${formatCurrency(alert.old_value)} → ${formatCurrency(alert.new_value)}`;
  if (alert.alert_type === "stock_spike") return "Went out of stock";
  return "A different seller took the Buy Box";
}

export default function Alerts() {
  const toast = useToast();
  const [type, setType] = useState("");
  const [state, setState] = useState("open");
  const [page, setPage] = useState(0);
  const [busy, setBusy] = useState("");
  useEffect(() => setPage(0), [type, state]);

  const acknowledged = state === "all" ? undefined : state === "done";
  const { data, total, error, initialLoading, reload } = useApi("/alerts", { type, acknowledged, limit: PAGE_SIZE, offset: page * PAGE_SIZE });

  const refreshAll = () => { invalidate("/alerts"); invalidate("/analytics"); reload(); };

  const toggle = async (alert) => {
    setBusy(alert.id);
    try {
      await api.patch(`/alerts/${alert.id}`, { acknowledged: !alert.acknowledged });
      refreshAll();
    } catch (err) {
      toast.error("Could not update alert", err.message);
    } finally { setBusy(""); }
  };

  const acknowledgeAll = async () => {
    setBusy("all");
    try {
      const result = await api.post("/alerts/acknowledge-all", undefined, { });
      toast.success("Alerts acknowledged", `${result.updated} alert(s) marked as handled.`);
      refreshAll();
    } catch (err) { toast.error("Could not acknowledge alerts", err.message); }
    finally { setBusy(""); }
  };

  const runCheck = async () => {
    setBusy("check");
    try {
      const result = await api.post("/alerts/check");
      toast[result.created ? "warning" : "success"]("Alert check complete", result.created ? `${result.created} new alert(s) raised.` : "No new alerts.");
      refreshAll();
    } catch (err) { toast.error("Alert check failed", err.message); }
    finally { setBusy(""); }
  };

  const exportCsv = async () => {
    setBusy("csv");
    try { await downloadFile("/alerts/export.csv", { type, acknowledged }, "alerts.csv"); toast.success("Export ready", "The CSV file was downloaded."); }
    catch (err) { toast.error("Export failed", err.message); }
    finally { setBusy(""); }
  };

  return (
    <div className="page">
      <PageHeader title="Alerts" subtitle="Price drops, Buy Box changes and stock-outs detected from stored snapshots."
        actions={<>
          <Button icon={RefreshCw} loading={busy === "check"} onClick={runCheck}>Run check</Button>
          <Button icon={Download} loading={busy === "csv"} onClick={exportCsv}>Export CSV</Button>
          <Button variant="primary" icon={CheckCheck} loading={busy === "all"} disabled={!total || state === "done"} onClick={acknowledgeAll}>Acknowledge all</Button>
        </>} />
      <Card flush>
        <div className="toolbar">
          <Segmented label="Alert type" options={TYPES} value={type} onChange={setType} />
          <span className="toolbar-spacer" />
          <Segmented label="Status" options={STATES} value={state} onChange={setState} />
        </div>
        {error && !data ? <ErrorState error={error} onRetry={reload} /> : initialLoading ? <SkeletonRows rows={7} columns={5} /> : data?.length ? (
          <>
            <div className="table-wrap"><table className="table">
              <thead><tr><th>Type</th><th>Product</th><th>Change</th><th>Triggered</th><th>Notified</th><th /></tr></thead>
              <tbody>{data.map((alert) => {
                const meta = ALERT_TYPES[alert.alert_type] || { label: alert.alert_type, tone: "" };
                return (
                  <tr key={alert.id} style={{ opacity: alert.acknowledged ? 0.6 : 1 }}>
                    <td><Badge tone={meta.tone} dot>{meta.label}</Badge></td>
                    <td><Link to={`/app/products/${alert.asin}`} className="table-title">{alert.title || "Untitled listing"}</Link><div className="table-sub"><span className="asin-chip">{alert.asin}</span></div></td>
                    <td className={alert.alert_type === "price_drop" ? "num nowrap" : "nowrap"}>{describe(alert)}</td>
                    <td className="muted" title={formatDateTime(alert.triggered_at)}>{formatRelative(alert.triggered_at)}</td>
                    <td>{alert.notified ? <Badge tone="success">Sent</Badge> : <Badge>Not sent</Badge>}</td>
                    <td className="align-right"><Button size="sm" icon={alert.acknowledged ? Undo2 : Check} loading={busy === alert.id} onClick={() => toggle(alert)}>{alert.acknowledged ? "Reopen" : "Acknowledge"}</Button></td>
                  </tr>
                );
              })}</tbody>
            </table></div>
            <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPage={setPage} />
          </>
        ) : (
          <EmptyState mood="happy" title={state === "open" ? "Inbox zero" : "No alerts here"}>
            {state === "open" ? "Nothing needs your attention. Alerts appear when prices drop, the Buy Box moves or stock runs out." : "No alerts match these filters."}
          </EmptyState>
        )}
      </Card>
    </div>
  );
}
