"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { KeyRound, Loader2, Plus, Trash2 } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { CategoryLabel } from "@/components/shared/category-icon";
import { CategorySelect } from "@/components/shared/category-select";
import { fieldAria } from "@/components/shared/form-field";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, errorMessage } from "@/lib/api";
import { useCategories, useCategoryMap, useCreateRule, useDeleteRule, useRules } from "@/lib/queries";
import { ruleSchema, type RuleFormValues } from "@/lib/schemas";

const CHAIN_STEPS = [
  { title: "Your keyword rules", text: "Checked first. The longest matching keyword wins." },
  { title: "Known merchants", text: "Statement names like “AMZN MKTP” or “SWGY” are recognised." },
  { title: "Your past choices", text: "If you filed the same description by hand before, it goes there again." },
  { title: "Uncategorized", text: "Anything left over, ready for you to sort." },
];

export function RulesPanel() {
  const { data: rules, error, isPending, refetch } = useRules();
  const categories = useCategories().data ?? [];
  const categoryMap = useCategoryMap();
  const create = useCreateRule();
  const remove = useDeleteRule();
  const { register, handleSubmit, control, reset, setError, formState } = useForm<RuleFormValues>({
    resolver: zodResolver(ruleSchema),
    defaultValues: { keyword: "", category_id: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await create.mutateAsync(values);
      toast.success(`Rule added for “${values.keyword.trim().toLowerCase()}”`);
      reset({ keyword: "", category_id: values.category_id });
    } catch (e) {
      if (e instanceof ApiError && e.code === "conflict") {
        setError("keyword", { message: e.message });
      } else {
        toast.error("Couldn't add rule", { description: errorMessage(e) });
      }
    }
  });

  const sorted = [...(rules ?? [])].sort((a, b) => a.keyword.localeCompare(b.keyword));

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Keyword rules</CardTitle>
            <CardDescription>
              Expenses whose description contains a keyword are filed under its category.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="grid gap-5">
          <form onSubmit={onSubmit} noValidate className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-start">
            <div className="grid gap-1.5">
              <Label htmlFor="rule-keyword" className="sr-only">
                Keyword
              </Label>
              <Input
                {...fieldAria("rule-keyword", formState.errors.keyword?.message)}
                placeholder="Keyword, e.g. uber"
                autoComplete="off"
                {...register("keyword")}
              />
              {formState.errors.keyword ? (
                <p id="rule-keyword-error" role="alert" className="text-xs text-destructive">
                  {formState.errors.keyword.message}
                </p>
              ) : null}
            </div>
            <div className="grid gap-1.5">
              <Controller
                control={control}
                name="category_id"
                render={({ field }) => (
                  <CategorySelect
                    label="Category for this keyword"
                    value={field.value}
                    onChange={field.onChange}
                    categories={categories.filter((c) => !c.is_system)}
                    invalid={Boolean(formState.errors.category_id)}
                  />
                )}
              />
              {formState.errors.category_id ? (
                <p role="alert" className="text-xs text-destructive">
                  {formState.errors.category_id.message}
                </p>
              ) : null}
            </div>
            <Button type="submit" disabled={formState.isSubmitting}>
              {formState.isSubmitting ? <Loader2 className="animate-spin" /> : <Plus />}
              Add rule
            </Button>
          </form>

          {isPending ? (
            <div className="grid gap-2">
              {Array.from({ length: 5 }, (_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : error ? (
            <ErrorState error={error} onRetry={() => void refetch()} />
          ) : sorted.length === 0 ? (
            <EmptyState
              icon={KeyRound}
              title="No keyword rules"
              description="Add one above, for example “netflix” for Subscriptions."
            />
          ) : (
            <ul className="divide-y rounded-lg border">
              {sorted.map((rule) => {
                const category = categoryMap.get(rule.category_id);
                return (
                  <li key={rule.id} className="flex items-center gap-3 px-4 py-2.5">
                    <code className="rounded bg-muted px-1.5 py-0.5 text-[13px]">{rule.keyword}</code>
                    <span className="text-muted-foreground" aria-hidden="true">
                      files under
                    </span>
                    <span className="min-w-0 flex-1 text-sm">
                      {category ? <CategoryLabel name={category.name} color={category.color} /> : "—"}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Delete rule ${rule.keyword}`}
                      onClick={() =>
                        remove.mutate(rule.id, {
                          onSuccess: () => toast.success(`Rule “${rule.keyword}” deleted`),
                          onError: (e) => toast.error("Couldn't delete", { description: errorMessage(e) }),
                        })
                      }
                    >
                      <Trash2 />
                    </Button>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card className="h-fit">
        <CardHeader>
          <CardTitle>How expenses get a category</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="grid gap-4">
            {CHAIN_STEPS.map((step, index) => (
              <li key={step.title} className="flex gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary tabular">
                  {index + 1}
                </span>
                <div>
                  <p className="text-sm font-medium">{step.title}</p>
                  <p className="text-sm text-muted-foreground">{step.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}
