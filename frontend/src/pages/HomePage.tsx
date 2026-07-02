import { LayoutDashboard } from "lucide-react";
import { PagePlaceholder } from "@/pages/PagePlaceholder";

export function HomePage() {
  return (
    <PagePlaceholder
      title="Dashboard"
      description="Overview metrics, recent activity, and engineering change status will appear here."
      icon={LayoutDashboard}
    />
  );
}
