import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import type { QuickAction } from "@/data/dashboardData";
import { DashboardCard } from "@/components/dashboard/DashboardCard";

type QuickActionsProps = {
  actions: QuickAction[];
};

export function QuickActions({ actions }: QuickActionsProps) {
  return (
    <DashboardCard title="Quick actions" description="Common workspace shortcuts.">
      <div className="grid gap-3 sm:grid-cols-2">
        {actions.map((action) => (
          <Link
            key={action.path}
            to={action.path}
            className="group rounded-md border p-4 transition-colors hover:bg-muted"
          >
            <div className="flex items-start justify-between gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <action.icon className="h-5 w-5" />
              </span>
              <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
            </div>
            <p className="mt-4 text-sm font-medium">{action.label}</p>
            <p className="mt-1 text-sm text-muted-foreground">{action.description}</p>
          </Link>
        ))}
      </div>
    </DashboardCard>
  );
}
