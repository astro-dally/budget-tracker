/** Zod schemas for forms. Amounts stay strings end-to-end to avoid float rounding. */
import { z } from "zod";

export const AUTO_CATEGORY = "auto";
export const NO_CATEGORY = "none";

const amount = z
  .string()
  .trim()
  .min(1, "Enter an amount")
  .regex(/^\d{1,10}(\.\d{1,2})?$/, "Use a number like 250 or 99.50")
  .refine((value) => Number(value) > 0, "Amount must be greater than zero");

const isoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Pick a date");

export const transactionSchema = z.object({
  type: z.enum(["expense", "income"]),
  amount,
  description: z
    .string()
    .trim()
    .min(1, "Add a short description")
    .max(200, "Keep it under 200 characters"),
  occurred_on: isoDate,
  category_id: z.string(),
});
export type TransactionFormValues = z.infer<typeof transactionSchema>;

export const categorySchema = z.object({
  name: z.string().trim().min(1, "Give the category a name").max(50, "Keep it under 50 characters"),
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Pick a colour"),
  icon: z.string().min(1),
  monthly_limit: z
    .string()
    .trim()
    .refine((v) => v === "" || /^\d{1,10}(\.\d{1,2})?$/.test(v), "Use a number like 5000")
    .refine((v) => v === "" || Number(v) > 0, "A limit must be greater than zero"),
});
export type CategoryFormValues = z.infer<typeof categorySchema>;

export const ruleSchema = z.object({
  keyword: z.string().trim().min(2, "At least 2 characters").max(50, "Keep it under 50 characters"),
  category_id: z.string().min(1, "Choose a category"),
});
export type RuleFormValues = z.infer<typeof ruleSchema>;

export const recurringSchema = z
  .object({
    description: z.string().trim().min(1, "Add a description").max(200),
    amount,
    type: z.enum(["expense", "income"]),
    frequency: z.enum(["daily", "weekly", "monthly"]),
    start_date: isoDate,
    end_date: z.string(),
    category_id: z.string(),
  })
  .refine((v) => v.end_date === "" || v.end_date >= v.start_date, {
    message: "End date can't be before the start date",
    path: ["end_date"],
  });
export type RecurringFormValues = z.infer<typeof recurringSchema>;
