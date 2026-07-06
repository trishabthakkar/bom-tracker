import { Badge } from "@/components/ui/badge";

type RiskBadgeProps = {
  level: string;
};

export function RiskBadge({ level }: RiskBadgeProps) {
  const normalized = level.toLowerCase();
  const variant =
    normalized === "high" ? "destructive" : normalized === "medium" ? "warning" : "success";

  return <Badge variant={variant}>{level} risk</Badge>;
}
