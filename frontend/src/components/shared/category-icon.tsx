import {
  Baby,
  BookOpen,
  Car,
  CircleHelp,
  Clapperboard,
  Coffee,
  Dumbbell,
  Gift,
  GraduationCap,
  HeartPulse,
  House,
  Landmark,
  Plane,
  Repeat,
  ShoppingBag,
  ShoppingCart,
  Smartphone,
  Tag,
  Utensils,
  Wallet,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const CATEGORY_ICONS: Record<string, LucideIcon> = {
  house: House,
  utensils: Utensils,
  car: Car,
  repeat: Repeat,
  "shopping-bag": ShoppingBag,
  "shopping-cart": ShoppingCart,
  clapperboard: Clapperboard,
  zap: Zap,
  "heart-pulse": HeartPulse,
  plane: Plane,
  coffee: Coffee,
  dumbbell: Dumbbell,
  "graduation-cap": GraduationCap,
  gift: Gift,
  smartphone: Smartphone,
  baby: Baby,
  "book-open": BookOpen,
  landmark: Landmark,
  wallet: Wallet,
  tag: Tag,
  "circle-help": CircleHelp,
};

export const CATEGORY_COLORS = [
  "#5b6cf0",
  "#3b8fd9",
  "#2fa69a",
  "#5fa564",
  "#e2a23b",
  "#ea7a45",
  "#df5f86",
  "#9b6cf0",
  "#64748b",
];

/** A tinted rounded square holding the category's icon. */
export function CategoryIcon({
  icon,
  color,
  size = "md",
  className,
}: {
  icon: string;
  color: string;
  size?: "sm" | "md";
  className?: string;
}) {
  const Icon = CATEGORY_ICONS[icon] ?? Tag;
  return (
    <span
      aria-hidden="true"
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-lg",
        size === "sm" ? "size-7" : "size-9",
        className,
      )}
      style={{ backgroundColor: `${color}1f`, color }}
    >
      <Icon className={size === "sm" ? "size-3.5" : "size-4"} />
    </span>
  );
}

/** Small coloured dot + name, used in tables and selects. */
export function CategoryLabel({ name, color }: { name: string; color: string }) {
  return (
    <span className="inline-flex min-w-0 items-center gap-2">
      <span className="size-2 shrink-0 rounded-full" style={{ backgroundColor: color }} />
      <span className="truncate">{name}</span>
    </span>
  );
}
