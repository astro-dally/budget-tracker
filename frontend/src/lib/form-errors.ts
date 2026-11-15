import type { FieldValues, Path, UseFormSetError } from "react-hook-form";
import { toast } from "sonner";
import { ApiError, errorMessage } from "@/lib/api";

/**
 * Show server-side validation errors next to the matching fields; anything
 * else becomes a toast.
 */
export function applyServerErrors<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  fields: ReadonlyArray<Path<T>>,
): void {
  if (error instanceof ApiError) {
    const matched = error.details.filter((d) => (fields as readonly string[]).includes(d.field));
    matched.forEach((d) => setError(d.field as Path<T>, { message: d.message }));
    if (matched.length > 0) return;
    if (error.code === "conflict") {
      const target = (["email", "name"] as const).find((f) => fields.includes(f as Path<T>));
      if (target) {
        setError(target as Path<T>, { message: error.message });
        return;
      }
    }
    if (error.code === "validation_error" && fields.includes("password" as Path<T>)) {
      setError("password" as Path<T>, { message: error.message });
      return;
    }
  }
  toast.error("Couldn't save", { description: errorMessage(error) });
}
