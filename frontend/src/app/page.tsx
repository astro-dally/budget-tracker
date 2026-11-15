"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";
import { Brand } from "@/components/layout/brand";
import { FeatureBento } from "@/components/marketing/feature-bento";
import { PaceSimulator } from "@/components/marketing/pace-simulator";
import { SiteNav } from "@/components/marketing/site-nav";
import { StatementMarquee } from "@/components/marketing/statement-marquee";
import { Button } from "@/components/ui/button";

const STEPS = [
  { title: "Create your account", text: "You start with common categories and smart keyword rules already set up." },
  { title: "Set monthly limits", text: "Give the categories you care about a budget. Add rent, salary and subscriptions once." },
  { title: "Spend, and get warned in time", text: "Record expenses as they happen. We file them and tap you on the shoulder at 80%." },
];

export default function LandingPage() {
  return (
    <div className="min-h-dvh overflow-x-hidden">
      <SiteNav />

      <main id="main">
        <section className="mx-auto grid max-w-6xl items-center gap-14 px-4 pt-12 pb-24 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:pt-20">
          <div className="animate-rise">
            <span className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground">
              <Sparkles className="size-3.5 text-primary" /> Free for everyone. No card, no spreadsheet.
            </span>
            <h1 className="mt-6 font-display text-[clamp(2.75rem,7vw,5.5rem)] leading-[0.95] font-semibold tracking-[-0.045em]">
              Catch overspending while it&apos;s still happening.
            </h1>
            <p className="mt-6 max-w-lg text-lg text-muted-foreground">
              Most apps tell you on the 31st. Budget Tracker watches your pace every day, files your
              expenses for you, and warns you at 80% of a budget, not after you&apos;ve blown it.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg" className="h-12 rounded-xl px-6 text-base">
                <Link href="/signup">
                  Create a free account <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="h-12 rounded-xl px-6 text-base">
                <Link href="/login">Try a demo account</Link>
              </Button>
            </div>
          </div>
          <div className="mb-16 animate-rise [animation-delay:150ms] lg:mb-0">
            <PaceSimulator />
          </div>
        </section>

        <section aria-label="Automatic categorisation" className="border-y bg-muted/40 py-6">
          <StatementMarquee />
        </section>

        <section id="features" className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
          <div className="max-w-2xl">
            <h2 className="font-display text-4xl font-semibold tracking-[-0.03em] sm:text-5xl">
              Everything a budget should have done all along.
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Built for real spending: messy bank descriptions, rent on the 1st, and the dinner that
              tipped you over.
            </p>
          </div>
          <div className="mt-12">
            <FeatureBento />
          </div>
        </section>

        <section id="how" className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
          <h2 className="font-display text-4xl font-semibold tracking-[-0.03em] sm:text-5xl">Up and running in three steps.</h2>
          <ol className="mt-12 grid gap-6 md:grid-cols-3">
            {STEPS.map((step, index) => (
              <li key={step.title} className="border-t-2 border-foreground pt-6">
                <span className="font-display text-6xl font-semibold text-primary tabular">{index + 1}</span>
                <h3 className="mt-4 text-lg font-semibold">{step.title}</h3>
                <p className="mt-2 text-muted-foreground">{step.text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
          <div className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-ledger to-ledger-2 px-6 py-16 text-center text-white sm:px-16">
            <div className="ledger-grid absolute inset-0" aria-hidden="true" />
            <div className="pointer-events-none absolute -bottom-40 left-1/2 size-[36rem] -translate-x-1/2 rounded-full bg-lime/20 blur-3xl" aria-hidden="true" />
            <div className="relative">
              <h2 className="mx-auto max-w-3xl font-display text-4xl font-semibold tracking-[-0.03em] sm:text-6xl">
                Your next overspend is already on its way. Catch it.
              </h2>
              <div className="mt-10 flex flex-wrap justify-center gap-3">
                <Button asChild size="lg" className="h-12 rounded-xl bg-lime px-6 text-base text-ledger hover:bg-lime/90">
                  <Link href="/signup">
                    Start for free <ArrowRight />
                  </Link>
                </Button>
                <Button asChild size="lg" variant="ghost" className="h-12 rounded-xl px-6 text-base text-white hover:bg-white/10 hover:text-white">
                  <Link href="/login">Explore a demo</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:px-6">
          <Brand href="/" />
          <p>Built with FastAPI and Next.js. Your data never leaves your account.</p>
        </div>
      </footer>
    </div>
  );
}
