"use client";

import { useEffect, useRef, useState } from "react";

/** Animate a number towards `target` (ease-out), skipping animation for reduced motion. */
export function useCountUp(target: number, duration = 900): number {
  const [value, setValue] = useState(target);
  const from = useRef(0);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setValue(target);
      from.current = target;
      return;
    }
    const start = performance.now();
    const origin = from.current;
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      setValue(origin + (target - origin) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
      else from.current = target;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);

  return value;
}
