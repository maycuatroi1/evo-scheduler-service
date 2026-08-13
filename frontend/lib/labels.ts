export const TIER_LABELS: Record<string, string> = {
  culture: "Văn hóa",
  vocational: "Nghề",
  both: "Cả hai",
};

export const SESSION_TYPE_LABELS: Record<string, string> = {
  theory: "Lý thuyết",
  practice: "Thực hành",
};

export function tierLabel(tier?: string | null): string {
  if (!tier) return "Chưa phân khối";
  return TIER_LABELS[tier] ?? tier;
}

export function tierColor(tier?: string | null) {
  switch (tier) {
    case "culture":
      return {
        dot: "bg-primary",
        badge: "bg-primary/10 text-primary border-primary/30",
        bar: "bg-primary",
        soft: "bg-primary/5",
      };
    case "vocational":
      return {
        dot: "bg-accent",
        badge: "bg-accent/10 text-accent border-accent/30",
        bar: "bg-accent",
        soft: "bg-accent/5",
      };
    default:
      return {
        dot: "bg-foreground/40",
        badge: "bg-foreground/10 text-foreground/70 border-border",
        bar: "bg-foreground/40",
        soft: "bg-foreground/5",
      };
  }
}

export function sessionTypeLabel(type: string): string {
  if (type === "TH") return SESSION_TYPE_LABELS.practice;
  return SESSION_TYPE_LABELS.theory;
}
