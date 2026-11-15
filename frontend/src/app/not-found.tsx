import { Compass } from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <EmptyState
      icon={Compass}
      title="Page not found"
      description="The page you're looking for doesn't exist or has moved."
      action={
        <Button asChild>
          <Link href="/">Go to the home page</Link>
        </Button>
      }
      className="py-24"
    />
  );
}
