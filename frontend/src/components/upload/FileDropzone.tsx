import { ChangeEvent, DragEvent, KeyboardEvent, useRef, useState } from "react";
import { FileUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type FileDropzoneProps = {
  accept: string;
  acceptedLabels: string[];
  maxSizeMb: number;
  disabled?: boolean;
  onFileSelected: (file: File) => void;
};

export function FileDropzone({
  accept,
  acceptedLabels,
  maxSizeMb,
  disabled = false,
  onFileSelected,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragging, setDragging] = useState(false);

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (file) {
      onFileSelected(file);
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);

    if (!disabled) {
      handleFiles(event.dataTransfer.files);
    }
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    handleFiles(event.target.files);
    event.target.value = "";
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (disabled) {
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      inputRef.current?.click();
    }
  }

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      aria-label={`Upload file. Accepted formats: ${acceptedLabels.join(", ")}. Maximum size ${maxSizeMb} MB.`}
      className={cn(
        "flex min-h-72 flex-col items-center justify-center rounded-lg border border-dashed bg-muted/30 p-6 text-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        dragging && "border-primary bg-primary/5",
        disabled && "cursor-not-allowed opacity-60",
      )}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) {
          setDragging(true);
        }
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onKeyDown={handleKeyDown}
    >
      <input
        ref={inputRef}
        className="hidden"
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={handleInputChange}
      />
      <div className="flex h-12 w-12 items-center justify-center rounded-md bg-card shadow-sm">
        <FileUp className="h-6 w-6 text-primary" />
      </div>
      <div className="mt-4 space-y-1">
        <p className="font-medium">Drop a file here</p>
        <p className="text-sm text-muted-foreground">
          {acceptedLabels.join(", ")} up to {maxSizeMb} MB
        </p>
      </div>
      <Button
        type="button"
        variant="outline"
        className="mt-5"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
      >
        Select file
      </Button>
    </div>
  );
}
