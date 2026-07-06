import { UploadPageShell } from "@/components/upload/UploadPageShell";

export function UploadEcoPage() {
  return (
    <UploadPageShell
      title="Upload ECO"
      description="Upload ECO PDFs or structured CSV/XLSX exports for future change interpretation workflows."
      category="eco"
      acceptedExtensions={[".pdf", ".csv", ".xlsx"]}
      acceptedLabels={["PDF", "CSV", "XLSX"]}
    />
  );
}
