import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { useToast } from "../components/Toast";
import { api } from "./api";
import { useAuth } from "./auth";
import { invalidate, refreshAll } from "./useApi";

const STORAGE_KEY = "bp.jobs";
const POLL_MS = 2000;
const CLEAR_AFTER_MS = 20000;
// "stalled" jobs are still polled: a slow crawl can recover, and a dead one stays dismissable.
const ACTIVE = new Set(["queued", "running", "stalled"]);

function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    // Only resume jobs from the last day; older ones are expired in Celery anyway.
    return saved.filter((job) => Date.now() - job.startedAt < 86_400_000);
  } catch {
    return [];
  }
}

function save(jobs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs));
  } catch {
    // storage unavailable; tracking continues in memory
  }
}

const JobsContext = createContext(null);

export function JobsProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const toast = useToast();
  const [jobs, setJobs] = useState(load);
  const notified = useRef(new Set());
  const jobsRef = useRef(jobs);
  jobsRef.current = jobs;

  useEffect(() => save(jobs), [jobs]);

  const startJob = useCallback((job) => {
    setJobs((current) => [
      { status: "queued", percent: null, done: 0, total: null, items: 0, startedAt: Date.now(), ...job },
      ...current.filter((item) => item.taskId !== job.taskId),
    ]);
  }, []);

  const dismiss = useCallback((taskId) => setJobs((current) => current.filter((job) => job.taskId !== taskId)), []);

  const activeKey = jobs
    .filter((job) => ACTIVE.has(job.status))
    .map((job) => job.taskId)
    .join(",");

  useEffect(() => {
    if (!isAuthenticated || !activeKey) return undefined;
    let cancelled = false;

    const tick = async () => {
      const active = jobsRef.current.filter((job) => ACTIVE.has(job.status));
      const updates = await Promise.all(
        active.map((job) =>
          api
            .get(`/crawl/tasks/${job.taskId}`)
            .then((data) => ({ taskId: job.taskId, data }))
            .catch(() => ({ taskId: job.taskId, stale: true })),
        ),
      );
      if (cancelled) return;
      setJobs((current) =>
        current.map((job) => {
          const update = updates.find((item) => item.taskId === job.taskId);
          if (!update) return job;
          if (update.stale) return { ...job, stale: true };
          const { status, percent, done, total, items, error, summary, idle_seconds: idle } = update.data;
          return { ...job, status, percent, done, total, items, error, summary, idle, stale: false };
        }),
      );
      updates.forEach(({ taskId, data }) => {
        if (!data || ACTIVE.has(data.status) || notified.current.has(taskId)) return;
        notified.current.add(taskId);
        const label = active.find((job) => job.taskId === taskId)?.label ?? "Job";
        if (data.status === "success") {
          toast.success(`${label} finished`, data.items ? `${data.items} item(s) saved.` : data.summary || "Completed.");
          invalidate();
          refreshAll();
        } else {
          toast.error(`${label} failed`, (data.error || "See the worker logs for details.").split("\n").pop());
        }
        setTimeout(() => dismiss(taskId), CLEAR_AFTER_MS);
      });
    };

    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [isAuthenticated, activeKey, toast, dismiss]);

  const value = useMemo(() => ({ jobs, startJob, dismiss }), [jobs, startJob, dismiss]);
  return <JobsContext.Provider value={value}>{children}</JobsContext.Provider>;
}

export function useJobs() {
  const context = useContext(JobsContext);
  if (!context) throw new Error("useJobs must be used inside <JobsProvider>");
  return context;
}
