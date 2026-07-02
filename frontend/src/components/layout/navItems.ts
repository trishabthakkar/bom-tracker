import {
  BarChart3,
  Clock3,
  FileText,
  GitBranch,
  LayoutDashboard,
  Settings,
  Upload,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type NavItem = {
  label: string;
  path: string;
  icon: LucideIcon;
};

export const navItems: NavItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Upload BOM", path: "/upload-bom", icon: Upload },
  { label: "Upload ECO", path: "/upload-eco", icon: FileText },
  { label: "Reports", path: "/reports", icon: BarChart3 },
  { label: "Dependency Graph", path: "/dependency-graph", icon: GitBranch },
  { label: "History", path: "/history", icon: Clock3 },
  { label: "Settings", path: "/settings", icon: Settings },
];
