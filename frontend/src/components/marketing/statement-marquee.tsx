import { ArrowRight } from "lucide-react";

const ITEMS: Array<[string, string, string]> = [
  ["POS 4411 AMZN MKTP IN", "Shopping", "#df5f86"],
  ["UBER *TRIP HELP.UBER.COM", "Transport", "#3b8fd9"],
  ["SWGY ORDER 88123", "Food & Dining", "#e2a23b"],
  ["NETFLIX.COM 866-579", "Subscriptions", "#9b6cf0"],
  ["SHARMA DAIRY", "Food & Dining", "#e2a23b"],
  ["BESCOM BILLDESK", "Utilities", "#2fa69a"],
  ["PVR INOX 2 TICKETS", "Entertainment", "#ea7a45"],
  ["APOLLO PHARMACY 0042", "Health", "#5fa564"],
];

function Chip({ statement, category, color }: { statement: string; category: string; color: string }) {
  return (
    <li className="flex shrink-0 items-center gap-3 rounded-full border bg-card px-4 py-2 text-sm shadow-sm">
      <span className="font-mono text-xs text-muted-foreground">{statement}</span>
      <ArrowRight className="size-3.5 text-muted-foreground" aria-hidden="true" />
      <span className="flex items-center gap-1.5 font-medium">
        <span className="size-2 rounded-full" style={{ backgroundColor: color }} />
        {category}
      </span>
    </li>
  );
}

/** Bank-statement gibberish turning into categories, on a slow loop. */
export function StatementMarquee() {
  return (
    <div className="relative overflow-hidden py-2 [mask-image:linear-gradient(90deg,transparent,black_10%,black_90%,transparent)]">
      <ul className="flex w-max animate-marquee gap-3 motion-reduce:animate-none" aria-label="Examples of automatic categorisation">
        {[...ITEMS, ...ITEMS].map(([statement, category, color], index) => (
          <Chip key={`${statement}-${index}`} statement={statement} category={category} color={color} />
        ))}
      </ul>
    </div>
  );
}
