"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Check, Loader2 } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { AuthLayout } from "@/components/auth/auth-layout";
import { PasswordField } from "@/components/auth/password-field";
import { fieldAria, FormField } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { applyServerErrors } from "@/lib/form-errors";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { useRedirectAfterAuth } from "@/lib/use-redirect-after-auth";

const schema = z.object({
  name: z.string().trim().min(1, "Tell us what to call you").max(60, "Keep it under 60 characters"),
  email: z.string().trim().min(1, "Enter your e-mail").email("Enter a valid e-mail"),
  password: z
    .string()
    .min(8, "Use at least 8 characters")
    .max(128, "Keep it under 128 characters")
    .regex(/[A-Za-z]/, "Include at least one letter")
    .regex(/\d/, "Include at least one number"),
});
type Values = z.infer<typeof schema>;

const CHECKS = [
  { label: "8+ characters", test: (p: string) => p.length >= 8 },
  { label: "A letter", test: (p: string) => /[A-Za-z]/.test(p) },
  { label: "A number", test: (p: string) => /\d/.test(p) },
];

function SignupForm() {
  const { register: signUp } = useAuth();
  const redirect = useRedirectAfterAuth();
  const { register, handleSubmit, watch, setError, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", password: "" },
  });
  const password = watch("password");
  const strength = CHECKS.filter((c) => c.test(password)).length;

  const onSubmit = handleSubmit(async (values) => {
    try {
      const user = await signUp(values.name, values.email, values.password);
      toast.success(`Welcome, ${user.name.split(" ")[0]}! Your starter categories are ready.`);
      redirect(user);
    } catch (error) {
      applyServerErrors(error, setError, ["name", "email", "password"]);
    }
  });

  return (
    <>
      <h1 className="text-4xl font-semibold">Create your account</h1>
      <p className="mt-2 text-muted-foreground">
        Free forever. You&apos;ll start with common categories and smart rules already set up.
      </p>

      <form onSubmit={onSubmit} noValidate className="mt-8 grid gap-4">
        <FormField id="signup-name" label="Your name" error={formState.errors.name?.message}>
          <Input
            {...fieldAria("signup-name", formState.errors.name?.message)}
            autoComplete="name"
            placeholder="Asha Rao"
            className="h-11"
            autoFocus
            {...register("name")}
          />
        </FormField>
        <FormField id="signup-email" label="E-mail" error={formState.errors.email?.message}>
          <Input
            {...fieldAria("signup-email", formState.errors.email?.message)}
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            className="h-11"
            {...register("email")}
          />
        </FormField>
        <FormField id="signup-password" label="Password" error={formState.errors.password?.message}>
          <PasswordField
            {...fieldAria("signup-password", formState.errors.password?.message)}
            autoComplete="new-password"
            {...register("password")}
          />
        </FormField>
        <div aria-live="polite">
          <div className="grid grid-cols-3 gap-1.5" aria-hidden="true">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 rounded-full bg-track transition-colors",
                  i < strength && (strength === 3 ? "bg-success" : "bg-warning"),
                )}
              />
            ))}
          </div>
          <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs">
            {CHECKS.map((check) => {
              const ok = check.test(password);
              return (
                <li key={check.label} className={cn("flex items-center gap-1", ok ? "text-success" : "text-muted-foreground")}>
                  <Check className={cn("size-3", !ok && "opacity-30")} aria-hidden="true" />
                  {check.label}
                  <span className="sr-only">{ok ? "(met)" : "(not met)"}</span>
                </li>
              );
            })}
          </ul>
        </div>
        <Button type="submit" size="lg" className="mt-2 h-11 rounded-xl text-base" disabled={formState.isSubmitting}>
          {formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
          Create account
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-primary underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
    </>
  );
}

export default function SignupPage() {
  return (
    <AuthLayout>
      <Suspense>
        <SignupForm />
      </Suspense>
    </AuthLayout>
  );
}
