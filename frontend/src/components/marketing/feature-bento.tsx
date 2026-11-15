import { CalendarClock, Lock, OctagonAlert, Radio, TriangleAlert, Wand2 } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

function Tile({
  title,
  body,
  icon,
  className,
  children,
}: {
  title: string;
  body: string;
  icon: ReactNode;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <article className={cn("relative flex flex-col overflow-hidden rounded-3xl border bg-card p-6", className)}>
      <span className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">{icon}</span>
      <h3 className="mt-5 font-display text-xl font-semibold tracking-tight">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">{body}</p>
      {children ? <div className="mt-6 flex-1">{children}</div> : null}
    </article>
  );
}

const CHAIN = ["Your keywords", "Known merchants", "Your past choices", "Uncategorized"];

export function FeatureBento() {
  return (
    <div className="grid gap-4 md:grid-cols-6">
      <Tile
        className="md:col-span-4"
        icon={<TriangleAlert className="size-5" />}
        title="A nudge at 80%. A shout at 100%."
        body="The moment an expense crosses a threshold you hear about it, once per category per month. No spam, no surprises on the 31st."
      >
        <div className="grid max-w-md gap-2">
          {[
            { icon: TriangleAlert, tone: "bg-warning/12 text-warning", title: "Budget warning", text: "Food & Dining passed 80%: ₹9,757 of ₹12,000." },
            { icon: OctagonAlert, tone: "bg-danger/12 text-danger", title: "Over budget", text: "Entertainment is over: ₹3,780 of ₹3,500." },
          ].map(({ icon: Icon, tone, title, text }, i) => (
            <div key={title} className="flex items-start gap-3 rounded-2xl border bg-background p-3 shadow-sm" style={{ marginLeft: i * 28 }}>
              <span className={cn("flex size-8 shrink-0 items-center justify-center rounded-lg", tone)}>
                <Icon className="size-4" />
              </span>
              <span className="text-sm">
                <span className="block font-semibold">{title}</span>
                <span className="text-muted-foreground">{text}</span>
              </span>
            </div>
          ))}
        </div>
      </Tile>

      <Tile
        className="md:col-span-2"
        icon={<Wand2 className="size-5" />}
        title="Files expenses for you"
        body="Four checks run in order until one knows where an expense belongs."
      >
        <ol className="grid gap-2">
          {CHAIN.map((step, index) => (
            <li key={step} className="flex items-center gap-3 rounded-xl bg-muted/70 px-3 py-2 text-sm">
              <span className="flex size-5 items-center justify-center rounded-full bg-primary text-[11px] font-semibold text-primary-foreground tabular">
                {index + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </Tile>

      <Tile
        className="md:col-span-2"
        icon={<CalendarClock className="size-5" />}
        title="Rent never sneaks up"
        body="Recurring payments are recorded on their due date. Daily, weekly or monthly."
      >
        <div className="grid grid-cols-7 gap-1.5" aria-hidden="true">
          {Array.from({ length: 28 }, (_, i) => (
            <span
              key={i}
              className={cn(
                "aspect-square rounded-md bg-muted",
                [0, 4, 7, 11, 14, 18, 21, 25].includes(i) && "bg-primary/25",
                i === 0 && "bg-primary",
              )}
            />
          ))}
        </div>
      </Tile>

      <Tile
        className="md:col-span-2"
        icon={<Radio className="size-5" />}
        title="Live, not end-of-month"
        body="Your dashboard and alerts update the instant you spend, on every open tab."
      >
        <div className="flex items-end gap-1.5" aria-hidden="true">
          {[34, 52, 41, 66, 58, 79, 72, 91].map((h, i) => (
            <span key={i} className="flex-1 rounded-t-md bg-gradient-to-t from-primary/30 to-primary" style={{ height: h }} />
          ))}
        </div>
      </Tile>

      <Tile
        className="md:col-span-2 bg-gradient-to-br from-ledger to-ledger-2 text-white [&_h3]:text-white [&_p]:text-white/70 [&>span]:bg-lime [&>span]:text-ledger"
        icon={<Lock className="size-5" />}
        title="Your data stays yours"
        body="Every account is walled off. Passwords are scrypt-hashed and sessions are signed."
      />
    </div>
  );
}
