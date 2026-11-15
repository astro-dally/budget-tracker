"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import Link from "next/link";
import { Suspense, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { AuthLayout } from "@/components/auth/auth-layout";
import { DemoAccounts } from "@/components/auth/demo-accounts";
import { PasswordField } from "@/components/auth/password-field";
import { fieldAria, FormField } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { DemoAccount } from "@/lib/types";
import { useRedirectAfterAuth } from "@/lib/use-redirect-after-auth";

const schema = z.object({
  email: z.string().trim().min(1, "Enter your e-mail").email("Enter a valid e-mail"),
  password: z.string().min(1, "Enter your password"),
});
type Values = z.infer<typeof schema>;

function LoginForm() {
  const { login } = useAuth();
  const redirect = useRedirectAfterAuth();
  const [formError, setFormError] = useState<string | null>(null);
  const [demoPending, setDemoPending] = useState<string | null>(null);
  const { register, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const signIn = async (email: string, password: string) => {
    setFormError(null);
    try {
      const user = await login(email, password);
      toast.success(`Welcome back, ${user.name.split(" ")[0]}`);
      redirect(user);
    } catch (error) {
      setFormError(errorMessage(error));
    }
  };

  const pickDemo = async (account: DemoAccount) => {
    setDemoPending(account.email);
    await signIn(account.email, account.password);
    setDemoPending(null);
  };

  return (
    <>
      <h1 className="text-4xl font-semibold">Welcome back</h1>
      <p className="mt-2 text-muted-foreground">Sign in to see how your month is going.</p>

      <form onSubmit={handleSubmit((v) => signIn(v.email, v.password))} noValidate className="mt-8 grid gap-4">
        {formError ? (
          <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError}
          </p>
        ) : null}
        <FormField id="login-email" label="E-mail" error={formState.errors.email?.message}>
          <Input
            {...fieldAria("login-email", formState.errors.email?.message)}
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            className="h-11"
            autoFocus
            {...register("email")}
          />
        </FormField>
        <FormField id="login-password" label="Password" error={formState.errors.password?.message}>
          <PasswordField
            {...fieldAria("login-password", formState.errors.password?.message)}
            autoComplete="current-password"
            {...register("password")}
          />
        </FormField>
        <Button type="submit" size="lg" className="mt-2 h-11 rounded-xl text-base" disabled={formState.isSubmitting}>
          {formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
          Sign in
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted-foreground">
        New here?{" "}
        <Link href="/signup" className="font-medium text-primary underline-offset-4 hover:underline">
          Create a free account
        </Link>
      </p>

      <DemoAccounts onPick={pickDemo} pending={demoPending} />
    </>
  );
}

export default function LoginPage() {
  return (
    <AuthLayout>
      <Suspense>
        <LoginForm />
      </Suspense>
    </AuthLayout>
  );
}
