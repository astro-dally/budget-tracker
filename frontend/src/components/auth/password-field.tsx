"use client";

import { Eye, EyeOff } from "lucide-react";
import { forwardRef, useState, type ComponentProps } from "react";
import { Input } from "@/components/ui/input";

/** Password input with a show/hide toggle. */
export const PasswordField = forwardRef<HTMLInputElement, ComponentProps<"input">>(
  function PasswordField(props, ref) {
    const [visible, setVisible] = useState(false);
    return (
      <div className="relative">
        <Input ref={ref} type={visible ? "text" : "password"} className="h-11 pr-11" {...props} />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          className="absolute top-1/2 right-2 -translate-y-1/2 rounded-md p-1.5 text-muted-foreground outline-none hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/40"
        >
          {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
        </button>
      </div>
    );
  },
);
