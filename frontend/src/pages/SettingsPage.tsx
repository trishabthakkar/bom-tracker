import { Settings } from "lucide-react";
import { PagePlaceholder } from "@/pages/PagePlaceholder";

export function SettingsPage() {
  return (
    <PagePlaceholder
      title="Settings"
      description="Workspace, user, and system configuration placeholder."
      icon={Settings}
    />
  );
}
