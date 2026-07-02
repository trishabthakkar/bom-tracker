import { Clock3 } from "lucide-react";
import { PagePlaceholder } from "@/pages/PagePlaceholder";

export function HistoryPage() {
  return (
    <PagePlaceholder
      title="History"
      description="Past uploads, analyses, and report revisions placeholder."
      icon={Clock3}
    />
  );
}
