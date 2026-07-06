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

export const metrics: Metric[] = [
  {
    label: "Uploads this week",
    value: "18",
    detail: "BOMs, ECOs, and manuals",
    trend: "+6 from last week",
  },
  {
    label: "Reports generated",
    value: "12",
    detail: "Impact reports prepared",
    trend: "4 awaiting review",
  },
  {
    label: "Open high risk changes",
    value: "3",
    detail: "Require engineering sign-off",
    trend: "1 due today",
  },
  {
    label: "Dependency checks",
    value: "46",
    detail: "Assemblies scanned",
    trend: "92% complete",
  },
];

export const recentUploads: RecentUpload[] = [
  {
    id: "upl-1042",
    filename: "MX-2400_drive_unit_bom_revC.xlsx",
    type: "BOM",
    uploadedBy: "Aisha Khan",
    uploadedAt: "Today, 10:24",
    status: "Validated",
  },
  {
    id: "upl-1041",
    filename: "ECO-7812 cooling manifold replacement.pdf",
    type: "ECO",
    uploadedBy: "Ravi Menon",
    uploadedAt: "Today, 09:10",
    status: "Processing",
  },
  {
    id: "upl-1039",
    filename: "Commissioning checklist line-7.pdf",
    type: "Manual",
    uploadedBy: "Maya Torres",
    uploadedAt: "Yesterday, 16:45",
    status: "Needs review",
  },
  {
    id: "upl-1037",
    filename: "Valve assembly service pack revB.csv",
    type: "BOM",
    uploadedBy: "Nolan Price",
    uploadedAt: "Yesterday, 11:32",
    status: "Validated",
  },
];

export const recentReports: RecentReport[] = [
  {
    id: "rep-882",
    title: "Cooling manifold ECO downstream impact",
    generatedAt: "Today, 11:02",
    risk: "High",
    affectedItems: 38,
    status: "Review",
  },
  {
    id: "rep-879",
    title: "Drive unit BOM revision C comparison",
    generatedAt: "Yesterday, 17:30",
    risk: "Medium",
    affectedItems: 21,
    status: "Ready",
  },
  {
    id: "rep-875",
    title: "Service manual torque spec update",
    generatedAt: "Monday, 14:05",
    risk: "Low",
    affectedItems: 7,
    status: "Draft",
  },
];

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

export const recentActivity: ActivityItem[] = [
  {
    id: "act-1",
    title: "Report marked for review",
    description: "Cooling manifold ECO flagged as high risk for commissioning.",
    time: "18 min ago",
  },
  {
    id: "act-2",
    title: "BOM validation completed",
    description: "MX-2400 drive unit BOM revision C passed structural checks.",
    time: "42 min ago",
  },
  {
    id: "act-3",
    title: "Manual uploaded",
    description: "Line-7 commissioning checklist queued for document mapping.",
    time: "Yesterday",
  },
  {
    id: "act-4",
    title: "Dependency graph refreshed",
    description: "46 assemblies indexed for downstream impact tracing.",
    time: "Yesterday",
  },
];
