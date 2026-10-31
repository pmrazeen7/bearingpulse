import React from "react";
import { AlertTriangle, CheckCircle2, X } from "lucide-react";

import { formatNumber } from "../lib/format";
import { useJobs } from "../lib/jobs";

const LABELS = {
  queued: "Queued — waiting for a worker",
  running: "Running",
  stalled: "Stalled",
  success: "Finished",
  failed: "Failed",
};

function idleText(seconds) {
  if (!seconds) return "";
  return seconds >= 120 ? `${Math.round(seconds / 60)} min` : `${seconds}s`;
}

function Progress({ job }) {
  const indeterminate = (job.status === "queued" || job.status === "running") && job.percent === null;
  const value = job.status === "success" ? 100 : (job.percent ?? 0);
  return (
    <div
      className={`progress ${indeterminate ? "is-indeterminate" : ""} progress-${job.status}`}
      role="progressbar"
      aria-label={`${job.label} progress`}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={indeterminate ? undefined : value}
    >
      <span style={{ width: indeterminate ? undefined : `${value}%` }} />
    </div>
  );
}

export default function JobTray() {
  const { jobs, dismiss } = useJobs();
  if (!jobs.length) return null;
  return (
    <aside className="job-tray" aria-label="Background jobs" aria-live="polite">
      {jobs.slice(0, 3).map((job) => {
        const finished = job.status === "success" || job.status === "failed";
        return (
          <section className={`job-card is-${job.status}`} key={job.taskId}>
            <header>
              <span className="job-title">
                {job.status === "success" && <CheckCircle2 size={15} className="job-ok" aria-hidden="true" />}
                {job.status === "failed" && <AlertTriangle size={15} className="job-bad" aria-hidden="true" />}
                {job.status === "stalled" && <AlertTriangle size={15} className="job-warn" aria-hidden="true" />}
                {job.label}
              </span>
              <span className="job-percent num">
                {job.status === "success" ? "100%" : job.percent !== null ? `${job.percent}%` : ""}
              </span>
              <button type="button" className="job-close" aria-label={`Dismiss ${job.label}`} onClick={() => dismiss(job.taskId)}>
                <X size={14} />
              </button>
            </header>
            <Progress job={job} />
            <footer>
              <span>{job.stale ? "Reconnecting…" : LABELS[job.status]}</span>
              {!finished && job.total ? (
                <span className="num">
                  {formatNumber(job.done)} / {formatNumber(job.total)} requests
                </span>
              ) : null}
              {job.items > 0 && <span className="num">{formatNumber(job.items)} saved</span>}
            </footer>
            {job.status === "failed" && job.error && <p className="job-error">{job.error.split("\n").pop()}</p>}
            {job.status === "stalled" && (
              <p className="job-warning">
                No progress for {idleText(job.idle)}. The worker was probably restarted while this ran. Dismiss it and run the job
                again; items already saved are kept.
              </p>
            )}
          </section>
        );
      })}
    </aside>
  );
}
