import { GitBranch } from "lucide-react";
import { PagePlaceholder } from "@/pages/PagePlaceholder";

export function DependencyGraphPage() {
  return (
    <PagePlaceholder
      title="Dependency Graph"
      description="Assembly and part relationship visualization placeholder."
      icon={GitBranch}
    />
  );
}
