import type { LucideIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type PagePlaceholderProps = {
  title: string;
  description: string;
  icon: LucideIcon;
};

export function PagePlaceholder({
  title,
  description,
  icon: Icon,
}: PagePlaceholderProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Workspace</p>
          <h1 className="text-2xl font-semibold tracking-normal">{title}</h1>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Icon className="h-5 w-5" />
            </span>
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid min-h-72 place-items-center rounded-md border border-dashed bg-muted/35 p-6 text-center">
            <div className="max-w-sm">
              <p className="font-medium">Placeholder content</p>
              <p className="mt-2 text-sm text-muted-foreground">
                This page is intentionally empty until the next implementation phase.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
