"use client";

import { OctagonAlert, TriangleAlert } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { formatMoney } from "@/lib/format";
import { cn } from "@/lib/utils";

const BUDGET = 12000;
const DAYS = 30;

interface SimAlert {
  id: number;
  level: "warning" | "critical";
  text: string;
}

function status(used: number, time: number) {
  if (used >= 100) return { label: "Over budget", tone: "bg-coral", fill: "from-orange-400 to-coral" };
  if (used >= 80) return { label: "Past 80% of budget", tone: "bg-gold", fill: "from-amber-300 to-gold" };
  if (used - time > 5) return { label: "Spending faster than the month", tone: "bg-gold", fill: "from-emerald-300 to-gold" };
  return { label: "On pace", tone: "bg-lime", fill: "from-emerald-300 to-lime" };
}

/**
 * Landing-page hero: a playable version of the dashboard's pace meter. Drag
 * the day and the amount spent; crossing 80% or 100% pops the same alerts the
 * app sends.
 */
export function PaceSimulator() {
  const [day, setDay] = useState(4);
  const [spent, setSpent] = useState(2600);
  const [alerts, setAlerts] = useState<SimAlert[]>([]);
  const previous = useRef(spent);
  const nextId = useRef(0);

  // One orchestrated intro: the month "plays" forward and spending races ahead.
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setDay(13);
      setSpent(9900);
      return;
    }
    const start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / 2200);
      const eased = 1 - (1 - t) ** 3;
      setDay(Math.round(4 + 9 * eased));
      setSpent(Math.round((2600 + 7300 * eased) / 50) * 50);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    const delay = window.setTimeout(() => (frame = requestAnimationFrame(tick)), 600);
    return () => {
      window.clearTimeout(delay);
      cancelAnimationFrame(frame);
    };
  }, []);

  useEffect(() => {
    const before = (previous.current / BUDGET) * 100;
    const after = (spent / BUDGET) * 100;
    previous.current = spent;
    const crossed: SimAlert[] = [];
    if (before < 80 && after >= 80) {
      crossed.push({ id: nextId.current++, level: "warning", text: `Food & Dining passed 80% of its budget: ${formatMoney(spent, { whole: true })} of ${formatMoney(BUDGET, { whole: true })}.` });
    }
    if (before < 100 && after >= 100) {
      crossed.push({ id: nextId.current++, level: "critical", text: `Food & Dining is over budget: ${formatMoney(spent, { whole: true })} of ${formatMoney(BUDGET, { whole: true })}.` });
    }
    if (crossed.length === 0) return;
    setAlerts((list) => [...crossed, ...list].slice(0, 3));
    const ids = crossed.map((a) => a.id);
    const timer = window.setTimeout(() => setAlerts((list) => list.filter((a) => !ids.includes(a.id))), 4200);
    return () => window.clearTimeout(timer);
  }, [spent]);

  const used = (spent / BUDGET) * 100;
  const time = (day / DAYS) * 100;
  const state = status(used, time);
  const projected = (spent / day) * DAYS;
  const remaining = BUDGET - spent;

  return (
    <div className="relative">
      <div className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-ledger to-ledger-2 p-6 text-white shadow-2xl shadow-ledger/30 sm:p-8">
        <div className="ledger-grid absolute inset-0" aria-hidden="true" />
        <div className="pointer-events-none absolute -top-24 -right-16 size-80 rounded-full bg-lime/25 blur-3xl" aria-hidden="true" />
        <div className="relative">
          <div className="flex items-center justify-between gap-3">
            <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium ring-1 ring-white/15">
              <span className={cn("size-2 rounded-full", state.tone)} />
              {state.label}
            </span>
            <span className="text-xs text-white/55">Food & Dining · try the sliders</span>
          </div>

          <p className="mt-6 font-display text-5xl font-semibold tracking-[-0.04em] tabular sm:text-6xl" aria-live="polite">
            {formatMoney(Math.abs(remaining), { whole: true })}
          </p>
          <p className="mt-1 text-sm text-white/65">{remaining >= 0 ? "left this month" : "over budget"}</p>

          <div className="mt-9">
            <div className="relative h-4 rounded-full bg-white/10 ring-1 ring-white/10">
              <div
                className={cn("absolute inset-y-0 left-0 rounded-full bg-gradient-to-r transition-[width] duration-200", state.fill)}
                style={{ width: `${Math.min(100, used)}%` }}
              />
              <div className="absolute -top-2 -bottom-2 w-0.5 -translate-x-1/2 bg-white" style={{ left: `${time}%` }}>
                <span className="absolute bottom-full left-1/2 mb-1.5 -translate-x-1/2 rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap text-ledger">
                  Day {day}
                </span>
              </div>
            </div>
            <p className="mt-3 text-xs text-white/60">
              At this pace you&apos;ll spend{" "}
              <span className={cn("font-semibold tabular", projected > BUDGET ? "text-coral" : "text-lime")}>
                {formatMoney(projected, { whole: true })}
              </span>{" "}
              by day {DAYS}.
            </p>
          </div>

          <div className="mt-8 grid gap-5 sm:grid-cols-2">
            <label className="grid gap-2 text-xs text-white/70">
              <span className="flex justify-between">
                Day of the month <span className="font-semibold text-white tabular">{day}</span>
              </span>
              <input type="range" min={1} max={DAYS} value={day} onChange={(e) => setDay(Number(e.target.value))} />
            </label>
            <label className="grid gap-2 text-xs text-white/70">
              <span className="flex justify-between">
                Spent so far <span className="font-semibold text-white tabular">{formatMoney(spent, { whole: true })}</span>
              </span>
              <input type="range" min={0} max={15000} step={50} value={spent} onChange={(e) => setSpent(Number(e.target.value))} />
            </label>
          </div>
        </div>
      </div>

      <ul aria-live="polite" className="pointer-events-none absolute top-full right-4 left-4 z-10 mt-3 grid gap-2 sm:right-6 sm:left-auto sm:w-80">
        {alerts.map((alert) => (
          <li
            key={alert.id}
            className="flex animate-toast items-start gap-3 rounded-2xl border bg-popover p-3 text-popover-foreground shadow-xl"
          >
            <span
              className={cn(
                "flex size-8 shrink-0 items-center justify-center rounded-lg",
                alert.level === "critical" ? "bg-danger/12 text-danger" : "bg-warning/12 text-warning",
              )}
            >
              {alert.level === "critical" ? <OctagonAlert className="size-4" /> : <TriangleAlert className="size-4" />}
            </span>
            <span className="text-sm">
              <span className="block font-semibold">{alert.level === "critical" ? "Over budget" : "Budget warning"}</span>
              <span className="text-muted-foreground">{alert.text}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
