import { UploadPageShell } from "@/components/upload/UploadPageShell";

export function UploadBomPage() {
  return (
    <UploadPageShell
      title="Upload BOM"
      description="Upload CSV or Excel BOM files so future parsing modules can normalize assemblies, parts, and dependencies."
      category="bom"
      acceptedExtensions={[".csv", ".xlsx"]}
      acceptedLabels={["CSV", "XLSX"]}
    />
  );
}
