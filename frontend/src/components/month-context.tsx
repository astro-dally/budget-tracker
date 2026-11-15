"use client";

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { currentMonth } from "@/lib/month";

interface MonthContextValue {
  month: string;
  setMonth: (month: string) => void;
}

const MonthContext = createContext<MonthContextValue | null>(null);

/** Shares the selected month across pages so switching pages keeps context. */
export function MonthProvider({ children }: { children: ReactNode }) {
  const [month, setMonth] = useState(currentMonth);
  const value = useMemo(() => ({ month, setMonth }), [month]);
  return <MonthContext.Provider value={value}>{children}</MonthContext.Provider>;
}

export function useSelectedMonth(): MonthContextValue {
  const value = useContext(MonthContext);
  if (!value) throw new Error("useSelectedMonth must be used inside MonthProvider");
  return value;
}
