import {
  BarChart3,
  FileText,
  GitBranch,
  Upload,
  type LucideIcon,
} from "lucide-react";

export type Metric = {
  label: string;
  value: string;
  detail: string;
  trend: string;
};

export type RecentUpload = {
  id: string;
  filename: string;
  type: "BOM" | "ECO" | "Manual";
  uploadedBy: string;
  uploadedAt: string;
  status: "Validated" | "Processing" | "Needs review";
};

export type RecentReport = {
  id: string;
  title: string;
  generatedAt: string;
  risk: "Low" | "Medium" | "High";
  affectedItems: number;
  status: "Ready" | "Draft" | "Review";
};

export type QuickAction = {
  label: string;
  description: string;
  path: string;
  icon: LucideIcon;
};

export type ActivityItem = {
  id: string;
  title: string;
  description: string;
  time: string;
};

export const quickActions: QuickAction[] = [
  {
    label: "Upload BOM",
    description: "Import a CSV or Excel bill of materials.",
    path: "/upload-bom",
    icon: Upload,
  },
  {
    label: "Upload ECO",
    description: "Capture an engineering change order.",
    path: "/upload-eco",
    icon: FileText,
  },
  {
    label: "View Reports",
    description: "Open generated impact reports.",
    path: "/reports",
    icon: BarChart3,
  },
  {
    label: "Open Graph",
    description: "Inspect assembly and part dependencies.",
    path: "/dependency-graph",
    icon: GitBranch,
  },
];
